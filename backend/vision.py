import ollama
import pyautogui
from io import BytesIO


MODEL = "llava"


def read_screen():

    try:

        # Take screenshot
        screenshot = pyautogui.screenshot()


        # Convert screenshot to bytes
        buffer = BytesIO()

        screenshot.save(
            buffer,
            format="PNG"
        )


        image_data = buffer.getvalue()


        response = ollama.chat(

            model=MODEL,

            messages=[
                {
                    "role": "user",
                    "content": "Look at this screen and describe what you see.",
                    "images": [
                        image_data
                    ]
                }
            ]

        )


        return response["message"]["content"]


    except Exception as e:

        return f"Vision error: {str(e)}"