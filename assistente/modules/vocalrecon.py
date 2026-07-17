import os
import io
import re
import shutil
import subprocess


#=========================
# WHISPER MODEL
# =========================

_whisper_model = None


# =========================
# STT OFFLINE (whisper)
# =========================


# =========================
# RILEVAMENTO GPU
# =========================

def vulkan_available():
    """Controlla presenza Vulkan."""
    try:
        result = subprocess.run(
            ["vulkaninfo", "--summary"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3
        )
        return result.returncode == 0

    except Exception:
        return False

# =========================
# CARICAMENTO WHISPER CPP
# =========================

def get_whisper_model():

    global _whisper_model

    if _whisper_model is None:

        from pywhispercpp.model import Model


        # directory principale del progetto
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        models_dir = os.path.join(
            base_dir,
            "models"
        )



        if vulkan_available():

            model_file = "ggml-medium.bin"
            print("[WHISPER] Vulkan trovato -> medium")

        else:

            model_file = "ggml-small.bin"
            print("[WHISPER] CPU -> small")


        model_path = os.path.join(
            models_dir,
            model_file
        )


        threads = int(
            os.getenv(
                "ASSISTENTE_WHISPER_THREADS",
                "4"
            )
        )


        _whisper_model = Model(
            model_path,
            n_threads=threads
        )


    return _whisper_model


def trascrivi_offline(audio):
    """Trascrive un oggetto sr.AudioData con whisper offline. Ritorna sempre una stringa (mai None)."""
    try:
        model = get_whisper_model()
        wav_bytes = io.BytesIO(audio.get_wav_data())
        segments, _info = model.transcribe(wav_bytes, language="it", beam_size=5, vad_filter=True)
        testo = " ".join(segment.text for segment in segments).strip()
        return testo
    except Exception as e:
        print(f"[STT] Errore whisper offline: {e}")
        return ""

def adattalingua(comando):

  # Modifica comandi recepiti con nomi diversi in italiano da portare poi fuori dalllo script
    correzioni = {
        r"\bmito\b": "mitology",
        r"\bmitolo\b": "mitology",
        r"\bcrita\b": "krita",
        r"\bcreta\b": "krita",
        r"\bconsole\b": "konsole",
        r"\bcaffeine\b": "kaffeine",
        r"\bcate\b": "kate",
        r"\bspegne\b": "spegni",
        r"\bspenge\b": "spengi",
        r"\bspinge\b": "spegni",
        r"\bspingi\b": "spegni"
    }

    for errato, corretto in correzioni.items():
        #comando = comando.replace(errato, corretto)
        comando = re.sub(errato, corretto, comando, flags=re.IGNORECASE)
    return comando
