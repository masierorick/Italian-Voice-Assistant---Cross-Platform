import platform
import subprocess
import speech_recognition as sr

radio_reference = None
aec_device = None


def aec_exists():

    if platform.system() != "Linux":
        return False

    result = subprocess.run(
        ["pactl", "list", "short", "sources"],
        capture_output=True,
        text=True
    )

    return "assistente_aec" in result.stdout

def move_existing_streams_to_aec():
    """Sposta tutte le applicazioni audio già in riproduzione (es. browser con
    RaiPlay già aperto) sul sink AEC, così vengono usate come riferimento
    e cancellate dal microfono anche se erano partite prima dell'assistente."""

    try:
        result = subprocess.run(
            ["pactl", "list", "sink-inputs", "short"],
            capture_output=True,
            text=True
        )

        for riga in result.stdout.strip().splitlines():
            if not riga:
                continue
            stream_id = riga.split()[0]

            subprocess.run([
                "pactl",
                "move-sink-input",
                stream_id,
                "assistente_aec_sink"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)

    except Exception as e:
        print("Impossibile spostare gli stream esistenti sull'AEC:", e)

def init_audio_filter():

    sistema = platform.system()

    if sistema == "Linux":
        return init_linux_aec()

    elif sistema == "Windows":
        return init_windows_aec()

    elif sistema == "Darwin":
        return init_macos_aec()

    return None



# ==========================
# LINUX PIPEWIRE AEC
# ==========================

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

        # Cattura anche le app audio già aperte
        move_existing_streams_to_aec()

        aec_device = find_audio_device("pulse")

        print(f"🎤 Linux AEC attivo: {aec_device}")

        return aec_device


    except Exception as e:
        print("AEC Linux non disponibile:", e)
        return None



# ==========================
# WINDOWS
# ==========================

def init_windows_aec():

    print("🎤 Windows AEC WebRTC")

    # per ora ritorna microfono standard
    # il filtro verrà inserito nel flusso PCM

    return None



# ==========================
# MACOS
# ==========================

def init_macos_aec():

    print("🎤 macOS AEC WebRTC")

    # per ora ritorna microfono standard

    return None



# ==========================
# TROVA MICROFONO
# ==========================

def find_audio_device(nome):

    devices = sr.Microphone.list_microphone_names()

    for index, device in enumerate(devices):

        if nome.lower() in device.lower():
            return index

    return None


def get_audio_source():

    sistema = platform.system()

    if sistema == "Linux":
        return get_linux_microphone()

    elif sistema == "Windows":
        return get_windows_microphone()

    elif sistema == "Darwin":
        return get_macos_microphone()

    return None

# ==========================
# MICROFONO PER SISTEMA
# ==========================

def get_linux_microphone():

    if aec_device is not None:
        return sr.Microphone(device_index=aec_device)

    return sr.Microphone()



def get_windows_microphone():

    # futuro backend WASAPI + AEC
    return sr.Microphone()



def get_macos_microphone():

    # futuro backend CoreAudio + AEC
    return sr.Microphone()


# ==========================
# RIFERIMENTO RADIO AEC
# ==========================

def set_radio_reference(stream):

    global radio_reference

    radio_reference = stream



def get_radio_reference():

    return radio_reference
