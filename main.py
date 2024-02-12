import asyncio
import os
import tempfile
import pyaudio
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
from pydub.playback import play
import torch
import numpy as np
from scipy.io.wavfile import write
import g4f
import webbrowser
import wave
import json
from pydub import effects

def play_wav(filename):
    # Open the WAV file
    wf = wave.open(filename, 'rb')

    # Create a PyAudio object
    p = pyaudio.PyAudio()

    # Open a stream
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Read data in chunks
    chunk_size = 1024
    data = wf.readframes(chunk_size)

    # Play the audio file by writing to the stream
    while data:
        stream.write(data)
        data = wf.readframes(chunk_size)

    # Cleanup
    stream.stop_stream()
    stream.close()
    p.terminate()


def save_wav(audio, sample_rate, path="output.wav"):
    audio_numpy = audio.cpu().numpy()
    scaled = np.int16(audio_numpy / np.max(np.abs(audio_numpy)) * 32767)
    write(path, sample_rate, scaled)


# Load Silero TTS model
def load_silero_model(model_id='v4_ru', device='cpu'):
    model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                              model='silero_tts',
                              language='ru',
                              speaker=model_id)
    model.to(device)
    return model


def text_to_speech(text, model, speaker='eugene', sample_rate=48000):
    if not text or len(text) > 5000:  # Assuming 5000 is a reasonable upper limit
        print("Invalid or too long text for TTS.")
        return
    try:
        audio = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, "speech.wav")
        save_wav(audio, sample_rate, path=temp_file)
        audio_segment = AudioSegment.from_wav(temp_file)
        play(audio_segment)
        os.remove(temp_file)
    except Exception as e:  # Catch any unexpected errors from TTS
        print(f"Error during text-to-speech synthesis: {e}")



# Async function to get response from g4f with a character limit
async def get_response_from_g4f(text, char_limit=250):
    response = await g4f.ChatCompletion.create_async(
        model=g4f.models.default,
        messages=[{"role": "user", "content": text}],
        provider=g4f.Provider.You,
    )
    # Truncate the response if it's longer than char_limit
    if response:
        truncated_response = response[:char_limit]
        return truncated_response
    else:
        return "Sorry, I could not generate a response."



# Main function
async def main():
    model_path = "vosk_small"
    if not os.path.exists(model_path):
        print(f"Please download and unpack the Vosk model '{model_path}' to the current directory.")
        exit(1)
    vosk_model = Model(model_path)
    silero_model = load_silero_model()  # Load once at the start
    rec = KaldiRecognizer(vosk_model, 16000)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
    print("Please speak your question into the microphone. Say 'exit' to stop.")
    play_wav(filename='run.wav')

    try:
        while True:
            data = stream.read(4096, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower()
                print("Recognized:", text)
                if 'включи музыку' in text:
                    webbrowser.open('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
                if "мяч" in text:
                    print("Выхожу...")
                    break
                try:
                    response = await get_response_from_g4f(text)
                except ValueError as e:
                    print(f"Encountered an error while fetching response: {e}")
                    response = "Sorry, there was an error fetching the response. Please try again."
                print("Response:", response)
                text_to_speech(response, silero_model)  # Use Silero TTS for speech synthesis
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


asyncio.run(main())
