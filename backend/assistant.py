import ollama

from memory import load_memory, save_memory
from vision import read_screen

from tools import (
    open_app,
    open_website,
    get_time,
    screenshot,
    volume_up,
    volume_down,
    mute_volume,
    lock_pc,
    shutdown_pc,
    restart_pc
)


MODEL = "qwen-9b-uncensored-local:latest"


# ================= MEMORY =================

messages = [
    {
        "role": "system",
        "content": """
You are FRIDAY, a personal AI assistant.

Your name is FRIDAY.
Never say you are Qwen.

You can control the computer.
You have vision ability.

Be helpful and concise.
"""
    }
]


# Load old memory without system messages

old_memory = load_memory()

for msg in old_memory:
    if msg.get("role") != "system":
        messages.append(msg)



# ================= COMMAND HANDLER =================

def check_command(message):

    msg = message.lower().strip()


    # -------- SYSTEM --------


    if "take screenshot" in msg or "screenshot" in msg:
        return screenshot()


    if "volume up" in msg:
        return volume_up()


    if "volume down" in msg:
        return volume_down()


    if "mute" in msg:
        return mute_volume()



    if (
        msg == "lock"
        or "lock pc" in msg
        or "lock computer" in msg
    ):
        return lock_pc()



    if "shutdown" in msg:
        return shutdown_pc()



    if "restart" in msg:
        return restart_pc()



    # -------- VISION --------


    vision_words = [

        "look at my screen",
        "read my screen",
        "what is on my screen",
        "what's on my screen",
        "what on my screen",
        "what do you see",
        "what can you see",
        "check my screen",
        "analyze screen",
        "describe screen",
        "look",
        "screen"

    ]


    for word in vision_words:

        if word in msg:

            return read_screen()



    # -------- WEBSITE --------


    if "http://" in msg or "https://" in msg:

        url = msg.replace("open","").strip()

        return open_website(url)



    # -------- APP --------


    if msg.startswith("open "):

        app = msg.replace("open ","").strip()

        return open_app(app)



    # -------- TIME --------


    if "time" in msg:

        return get_time()



    return None




# ================= CHAT =================


def chat(message):


    command = check_command(message)


    if command:

        return command



    messages.append(
        {
            "role":"user",
            "content":message
        }
    )


    response = ollama.chat(

        model=MODEL,

        messages=messages

    )


    reply = response["message"]["content"]



    messages.append(
        {
            "role":"assistant",
            "content":reply
        }
    )



    save_memory(messages[-20:])


    return reply