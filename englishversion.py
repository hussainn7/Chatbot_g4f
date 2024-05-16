import asyncio
import os
import requests
import io
import tkinter as tk
import threading
import queue
import speech_recognition as sr
import webbrowser
from pydub import AudioSegment
from pydub.playback import play
from tkinter import Canvas, Text, PhotoImage
import g4f

os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"

r = sr.Recognizer()

# Trigger word
trigger_word = "eva"

def listen_for_trigger():
    print("Listening for trigger word...")
    while True:
        with sr.Microphone() as source:
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio, language='en-US')
                print(f"Heard: {text.lower()}")
                if trigger_word in text.lower():
                    print("Trigger word detected. Listening for your message...")
                    return True, text
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"Could not request results; {e}")

def speak(text):
    url = "https://api.elevenlabs.io/v1/text-to-speech/4IMpsgIR3EIjHPezf4eG"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": "99250370294a2969dc2a5cdfec386b5d"
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        audio_data = io.BytesIO(response.content)
        song = AudioSegment.from_file(audio_data, format="mp3")
        play(song)
    else:
        print("Failed to generate speech. Status code:", response.status_code)
        print("Response:", response.text)

async def main(app):
    await asyncio.sleep(1)  # Small delay to avoid capturing immediate background noise
    while True:
        trigger_detected, trigger_text = listen_for_trigger()
        if trigger_detected:
            with sr.Microphone() as source:
                # app.safe_print_to_gui(f"Prompt: {trigger_text}")  # Print the prompt in the GUI
                app.safe_print_to_gui("Yes, I am listening...")
                # speak("Whatsup Nigga")
                audio = r.listen(source)
                try:
                    text = r.recognize_google(audio)
                    app.safe_print_to_gui(f"You said: {text}")  # Print the recognized text in the GUI
                    if 'music' in text.lower():
                        webbrowser.open('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
                        continue
                    response = await get_response_from_g4f(text)
                    print(f'Answer: {response}')
                    app.safe_print_to_gui(f"Answer: {response}")
                    speak(response)
                    # Print the response in the GUI
                except sr.UnknownValueError:
                    app.safe_print_to_gui("Could not understand the audio. Please try again.")
                except sr.RequestError as e:
                    app.safe_print_to_gui(f"Request failed; {e}")

async def get_response_from_g4f(text, char_limit=700):
    response = await g4f.ChatCompletion.create_async(
        model=g4f.models.default,
        messages=[{"role": "user", "content": text}],
        provider=g4f.Provider.PerplexityLabs,
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

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1250x720")
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
        self.background_image = PhotoImage(file="assets/image_1.png")  # Change path accordingly
        self.canvas.create_image(
            635.0,
            360.0,
            image=self.background_image
        )

        self.create_widgets()
        self.process_queue()

    def create_widgets(self):
        button_image_2 = PhotoImage(file="assets/button_2.png")  # Change path accordingly
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

        button_image_1 = PhotoImage(file="assets/button_1.png")  # Change path accordingly
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

        self.entry_image_1 = PhotoImage(file="assets/entry_1.png")  # Change path accordingly
        self.entry_bg_1 = self.canvas.create_image(
            401.0,
            360.0,
            image=self.entry_image_1
        )
        self.entry_1 = Text(
            self,
            bd=0,
            bg="#031149",  # Background color
            fg="white",  # Text/foreground color changed to white
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
            loop.run_until_complete(main(self))
        finally:
            loop.close()

    def process_queue(self):
        try:
            task = self.task_queue.get_nowait()
            task()
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def print_to_gui(self, message):
        self.entry_1.insert(tk.END, message + "\n")
        self.entry_1.see(tk.END)

    def safe_print_to_gui(self, message):
        self.task_queue.put(lambda: self.print_to_gui(message))


if __name__ == "__main__":
    app = Application()
    app.mainloop()
