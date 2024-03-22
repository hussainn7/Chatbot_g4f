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
import re
from pydub import effects
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
from num2words import num2words
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage
from pathlib import Path
from miio import AirPurifierMiot
import time

IP_ADDRESS = '192.168.0.127'
TOKEN = 'f96f0cf12eabbd10fec9ea64f4a241e0'
air_purifier = AirPurifierMiot(ip=IP_ADDRESS, token=TOKEN)


def play_wav(filename):
    wf = wave.open(filename, 'rb')

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    chunk_size = 1024
    data = wf.readframes(chunk_size)
    while data:
        stream.write(data)
        data = wf.readframes(chunk_size)

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


def text_to_speech(text, model, speaker='xenia', sample_rate=48000):
    if not text or len(text) > 5000:
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
    except Exception as e:
        print(f"Error during text-to-speech synthesis: {e}")


def replace_numbers_with_words(text):
    return re.sub(r'\b\d+\b', lambda x: num2words(int(x.group()), lang='ru'), text)


async def get_response_from_g4f(text, char_limit=700):
    response = await g4f.ChatCompletion.create_async(
        model=g4f.models.default,
        messages=[{"role": "user", "content": text}],
        provider=g4f.Provider.You,
    )
    if response:
        if len(response) <= char_limit:
            return response
        else:
            last_period_index = response[:char_limit].rfind('.')
            if last_period_index != -1:
                truncated_response = response[:last_period_index + 1]
            else:
                truncated_response = response[:char_limit]
            return truncated_response
    else:
        return "Sorry, I could not generate a response."


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("assets")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1720x720")
        self.configure(bg="#FFFFFF")

        self.task_queue = queue.Queue()

        self.canvas = Canvas(
            self,
            bg="#FFFFFF",
            height=720,
            width=1270,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )

        self.canvas.place(x=0, y=0)
        self.background_image = PhotoImage(file=relative_to_assets("image_1.png"))
        self.canvas.create_image(
            635.0,
            360.0,
            image=self.background_image
        )

        self.create_widgets()
        self.process_queue()

    def create_widgets(self):
        button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
        self.button_2 = tk.Button(
            self,
            image=button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=self.start_recognition,
            relief="flat"
        )
        self.button_2.image = button_image_2
        self.button_2.place(
            x=815.0,
            y=439.0,
            width=78.0,
            height=72.0
        )


        button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
        self.button_1 = tk.Button(
            self,
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.start_recognition,
            relief="flat"
        )
        self.button_1.image = button_image_1
        self.button_1.place(
            x=815.0,
            y=563.0,
            width=78.0,
            height=72.0
        )








        self.entry_image_1 = PhotoImage(file=relative_to_assets("entry_1.png"))
        self.entry_bg_1 = self.canvas.create_image(
            401.0,
            360.0,
            image=self.entry_image_1
        )
        self.entry_1 = Text(
            self,
            bd=0,
            bg="#CEF39E",
            fg="#000716",
            highlightthickness=0,
            wrap="word",  # Ensure text wraps within the widget
            font=("Open Sans", 18)  # Adjust font and size as needed
        )
        self.entry_1.place(
            x=0.0,
            y=0.0,
            width=802.0,
            height=718.0
        )

    def start_recognition(self):
        threading.Thread(target=self.run_async_main, daemon=True).start()
        print("Starting please wait... until you hear something")

    def run_async_main(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.async_main())
        finally:
            loop.close()

    async def async_main(self):
        try:
            print("MADE by \n SYED HUSSAIN AND SHARMA KOSHEL")
            model_path = "vosk_small"
            if not os.path.exists(model_path):
                print(f"Please download and unpack the Vosk model '{model_path}' to the current directory.")
                return
            vosk_model = Model(model_path)
            silero_model = load_silero_model()
            rec = KaldiRecognizer(vosk_model, 16000)
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
            print("Скажите свой вопрос, для остановки скажите  -  стоп")
            greeting_text = "Привет, я здесь чтобы помочь."
            text_to_speech(greeting_text, silero_model)

            try:
                while True:
                    data = stream.read(4096, exception_on_overflow=False)
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        text = result.get("text", "").lower()
                        print("Распознано:", text)
                        if "стоп" in text:
                            print("Выхожу...")
                            break
                        # if "какой сейчас качество воздуха" in text:
                        #     text_to_speech("В кыргызстане ужасный воздух", silero_model)
                        if 'воздух' in text:
                            air_purifier.on()
                            text_to_speech("Выполняю", silero_model)
                        if 'нет' in text:
                            air_purifier.off()
                            text_to_speech("Выключаю воздух", silero_model)
                        if "белка" in text:
                            command = re.sub("белка", "", text,
                                             flags=re.IGNORECASE).strip()
                            self.safe_print_to_gui(f"Команда: {command}")
                            if 'включи музыку' in command:
                                webbrowser.open('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
                                continue
                            try:
                                response = await get_response_from_g4f(command)
                            except ValueError as e:
                                print(f"Encountered an error while fetching response: {e}")
                                response = "Sorry, there was an error fetching the response. Please try again."
                            response = replace_numbers_with_words(response)
                            self.safe_print_to_gui(f"Ответ: {response}")
                            text_to_speech(response, silero_model)
            finally:
                stream.stop_stream()
                stream.close()
                p.terminate()
        except Exception as e:
            print(f"Unexpected error in async_main: {e}")

    def print_to_gui(self, message):
        self.entry_1.insert(tk.END, message + "\n")
        self.entry_1.see(tk.END)

    def process_queue(self):
        try:
            task = self.task_queue.get_nowait()
            task()
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def safe_print_to_gui(self, message):
        self.task_queue.put(lambda: self.print_to_gui(message))


if __name__ == "__main__":
    app = Application()
    app.mainloop()
