import pyttsx3
import threading

engine = pyttsx3.init()

engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)

lock = threading.Lock()


def speak(text):
    with lock:
        engine.stop()
        engine.say(text)
        engine.runAndWait()