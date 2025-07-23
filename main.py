import os
import time
import tempfile
import soundfile as sf
import numpy as np
from scipy.io.wavfile import write
import pygame
from google import genai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted
import threading
import queue
import io
import serial
import json
import sounddevice as sd  # moved to top-level import

GOOGLE_API_KEY = "YOUR-API-KEY"
os.environ["GEMINI_API_KEY"] = GOOGLE_API_KEY
client = genai.Client(api_key=GOOGLE_API_KEY)

ESP32_PORT = "/dev/ttyUSB0"
ESP32_BAUDRATE = 115200
esp32_serial = None

# Only eyes and mouth controlled by python
#You can also add other parts. 
SERVO_MAPPINGS = {
    "eye_right": 7,
    "eye_left":  8,
    "mouth":     9
}

def connect_esp32():
    global esp32_serial
    try:
        esp32_serial = serial.Serial(ESP32_PORT, ESP32_BAUDRATE, timeout=1)
        time.sleep(2)
        print(f"Connected to ESP32 on {ESP32_PORT}")
        return True
    except Exception as e:
        print(f"Failed to connect to ESP32: {e}")
        return False

def send_servo_command(servo_pin, angle, duration=0.5):
    if esp32_serial is None:
        print("ESP32 not connected")
        return False
    angle = max(0, min(180, angle))
    cmd = json.dumps({"servo": servo_pin, "angle": angle, "duration": duration}) + "\n"
    esp32_serial.write(cmd.encode())
    return True

def set_led_listening_state(is_listening):
    if esp32_serial:
        esp32_serial.write((json.dumps({"listening": is_listening}) + "\n").encode())

def open_mouth():
    send_servo_command(SERVO_MAPPINGS["mouth"], 70, 0.2)

def close_mouth():
    send_servo_command(SERVO_MAPPINGS["mouth"], 90, 0.3)

def animate_mouth_during_speech(audio_duration):
    if audio_duration <= 0:
        return
    mouth_positions = [70, 85, 75, 90, 80, 75, 85, 70, 80, 90]
    dur = max(0.1, audio_duration / len(mouth_positions))
    for i, pos in enumerate(mouth_positions):
        if i * dur >= audio_duration:
            break
        send_servo_command(SERVO_MAPPINGS["mouth"], pos, dur)
        time.sleep(dur)
    close_mouth()

def estimate_audio_duration(audio_data, sample_rate=24000, channels=2):
    try:
        total_samples = len(audio_data) // (2 * channels)
        return max(0.5, total_samples / sample_rate)
    except:
        return 2.0

pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
response_cache = {}

def get_cache_key(text):
    return hash(text.strip().lower())

def cache_response(text, audio_data, mime_type):
    response_cache[get_cache_key(text)] = (audio_data, mime_type)

def get_cached_response(text):
    return response_cache.get(get_cache_key(text))

def record_audio(fs=16000, channels=1):
    """
    Record audio from the microphone, starting when the user presses Enter,
    stopping when they press Enter again. Returns the path to a WAV file.
    """
    print("Press Enter to start recording...")
    input()
    print("Recording... press Enter again to stop.")
    set_led_listening_state(True)

    frames = []
    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    with sd.InputStream(samplerate=fs, channels=channels, dtype='int16', callback=callback):
        input()  # wait until Enter pressed again to stop

    set_led_listening_state(False)
    audio_data = np.concatenate(frames, axis=0)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    write(tmp.name, fs, audio_data)
    print(f"Saved recording to {tmp.name}")
    return tmp.name

def retry_with_backoff(func, max_retries=2, base_delay=1.0, **kwargs):
    last_exc = None
    for i in range(max_retries):
        try:
            return func(**kwargs)
        except Exception as e:
            last_exc = e
            if i < max_retries - 1:
                time.sleep(base_delay * (2 ** i))
    raise last_exc or RuntimeError("Max retries exceeded")

def convert_and_play_audio(audio_data: bytes, mime_type: str):
    try:
        arr = np.frombuffer(audio_data, dtype=np.int16)
        if arr.ndim == 1:
            arr = np.column_stack((arr, arr))
        buf = io.BytesIO()
        sf.write(buf, arr, samplerate=24000, format='WAV')
        buf.seek(0)
        pygame.mixer.music.load(buf)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        print(f"Playback error: {e}")

actor_prompt = """PROMPT""" #add your prompt here

tts_config = types.GenerateContentConfig(
    temperature=0.8,
    response_modalities=["audio"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
)

def process_tts_with_cache(text, result_queue):
    try:
        cached = get_cached_response(text)
        if cached:
            result_queue.put(cached)
            return
        tts_stream = retry_with_backoff(
            func=client.models.generate_content_stream,
            model="gemini-2.5-flash-preview-tts", 
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=text)])],
            config=tts_config
        )
        audio_data, mime_type = b"", None
        for chunk in tts_stream:
            if chunk.candidates and chunk.candidates[0].content.parts[0].inline_data:
                part = chunk.candidates[0].content.parts[0].inline_data
                mime_type = mime_type or part.mime_type
                audio_data += part.data
        cache_response(text, audio_data, mime_type)
        result_queue.put((audio_data, mime_type))
    except Exception as e:
        print(f"TTS Error: {e}")
        result_queue.put((None, None))

def main():
    if not connect_esp32():
        print("Cannot start without ESP32")
        return

    # Neutral positions for eyes & mouth only
    send_servo_command(SERVO_MAPPINGS["eye_left"],  90)
    send_servo_command(SERVO_MAPPINGS["eye_right"], 90)
    send_servo_command(SERVO_MAPPINGS["mouth"],     90)
    print("Actor Ready!")

    try:
        while True:
            # now records until you hit Enter twice
            path = record_audio()
            print("Processing…")
            uploaded = retry_with_backoff(func=client.files.upload, file=path)

            print("Generating response text…")
            response_stream = retry_with_backoff(
                func=client.models.generate_content_stream,
                model="gemini-2.5-flash",
                contents=[actor_prompt, uploaded]
            )
            full_text = "".join(
                part.text
                for chunk in response_stream if chunk.candidates
                for part in chunk.candidates[0].content.parts
                if hasattr(part, "text")
            ).strip()
            print("AI:", full_text)

            # TTS + mouth animation
            tts_q = queue.Queue()
            t = threading.Thread(target=process_tts_with_cache, args=(full_text, tts_q))
            t.start(); t.join()
            audio_data, mime = tts_q.get()
            if audio_data:
                dur = estimate_audio_duration(audio_data)
                mouth_t = threading.Thread(target=animate_mouth_during_speech, args=(dur,))
                mouth_t.start()
                convert_and_play_audio(audio_data, mime)
                mouth_t.join()

            os.remove(path)
            print("Ready for next. Press Ctrl+C to exit or hit Enter to record again.")
    except KeyboardInterrupt:
        print("Shutting down.")
        close_mouth()
        if esp32_serial:
            esp32_serial.close()
        pygame.mixer.quit()

if __name__ == "__main__":
    main()
