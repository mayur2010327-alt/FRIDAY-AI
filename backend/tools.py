import os
import subprocess
import webbrowser
import datetime
import pyautogui
import ctypes


# ================= APP CONTROL =================


def find_app(app_name):

    app_name = app_name.lower()

    paths = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"C:\Users\mayur\AppData\Local",
        r"C:\Users\mayur\AppData\Roaming"
    ]


    for path in paths:

        if not os.path.exists(path):
            continue


        for root, dirs, files in os.walk(path):

            for file in files:

                if file.endswith(".exe"):

                    name = file.replace(".exe","").lower()

                    if app_name in name:

                        return os.path.join(root,file)


    return None



def open_app(app):

    apps = {

        "chrome":
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",

        "vscode":
        r"C:\Users\mayur\AppData\Local\Programs\Microsoft VS Code\Code.exe",

        "notepad":
        "notepad.exe",

        "calculator":
        "calc.exe"

    }


    app = app.lower()


    if app in apps:

        subprocess.Popen(apps[app])

        return f"Opening {app}"



    location = find_app(app)


    if location:

        subprocess.Popen(location)

        return f"Found and opening {app}"



    return f"I could not find {app}"



# ================= WEBSITE =================


def open_website(site):

    webbrowser.open(site)

    return f"Opening {site}"



# ================= TIME =================


def get_time():

    now = datetime.datetime.now()

    return now.strftime(
        "Current time is %I:%M %p"
    )



# ================= SCREENSHOT + VISION =================


def screenshot():


    folder = "screenshots"


    if not os.path.exists(folder):

        os.makedirs(folder)



    filename = datetime.datetime.now().strftime(
        "screen_%H-%M-%S.png"
    )


    path = os.path.join(
        folder,
        filename
    )


    img = pyautogui.screenshot()


    img.save(path)



    return path



# ================= VOLUME =================


def volume_up():

    pyautogui.press("volumeup")

    return "Volume increased"



def volume_down():

    pyautogui.press("volumedown")

    return "Volume decreased"



def mute_volume():

    pyautogui.press("volumemute")

    return "Volume muted"



# ================= POWER CONTROL =================


def lock_pc():

    ctypes.windll.user32.LockWorkStation()

    return "PC locked"



def shutdown_pc():

    os.system(
        "shutdown /s /t 5"
    )

    return "Shutting down PC"



def restart_pc():

    os.system(
        "shutdown /r /t 5"
    )

    return "Restarting PC"