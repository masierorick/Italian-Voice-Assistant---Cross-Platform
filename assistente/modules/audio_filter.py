import platform
import subprocess
import speech_recognition as sr


aec_device = None

def aec_exists():

    result = subprocess.run(
        ["pactl", "list", "short", "sources"],
        capture_output=True,
        text=True
    )

    return "assistente_aec" in result.stdout

def init_audio_filter():

    sistema = platform.system()

    if sistema == "Linux":
        return init_linux_aec()

    elif sistema == "Windows":
        return init_windows_aec()

    elif sistema == "Darwin":
        return init_macos_aec()

    return None


def init_linux_aec():

    global aec_device

    try:
      if not aec_exists():

        subprocess.run([
            "pactl",
            "load-module",
            "module-echo-cancel",
            "aec_method=webrtc",
            "source_name=assistente_aec",
            "sink_name=assistente_aec_sink"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

        subprocess.run([
            "pactl",
            "set-default-source",
            "assistente_aec"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

        aec_device = find_audio_device("pulse")

        return aec_device

    except Exception as e:
        print("AEC non disponibile:", e)
        return None


def find_audio_device(nome):

    devices = sr.Microphone.list_microphone_names()

    for index, device in enumerate(devices):
        if nome.lower() in device.lower():
            return index

    return None


def get_microphone():

    return aec_device
