import os, subprocess, soundfile as sf
import time
from playsound import playsound
from gtts import gTTS

from modules.config import *
from modules.network import ONLINE_MODE

tts_end_time = 0


# =========================
# TTS OFFLINE (PIPER)
# =========================
def speak_piper(text):

    piper = os.getenv("ASSISTENTE_PIPER_BIN", "piper")
    model = os.getenv("ASSISTENTE_PIPER_MODEL", str(main_path / "models/piper/it_IT-riccardo-x_low.onnx"))
    output_wav = "response.wav"

    try:
        subprocess.run(
            [piper, "--model", model, "--output_file", output_wav],
            input=text.encode("utf-8"),
            check=True
        )

        playsound(output_wav)

    except Exception as e:
        print(f"[TTS] Errore Piper: {e}")

    finally:
        if os.path.exists(output_wav):
            os.remove(output_wav)



# =========================
# FUNZIONE PRINCIPALE TTS
# =========================
def speak(text):

    global parla_sintesi, tts_end_time

    parla_sintesi = True

    # Modalità online: usa Google TTS
    # Se fallisce passa automaticamente al TTS offline
    try:
      if ONLINE_MODE:
        try:
            tts = gTTS(text=text, lang="it")
            tts.save("response.mp3")
            playsound("response.mp3")
            os.remove("response.mp3")

        except Exception as e:
            print(f"[TTS] gTTS non disponibile: {e}")



      # Modalità offline
      else:
        speak_piper(text)


    finally:
        # lascia svuotare il buffer audio
        time.sleep(0.8)

        tts_end_time = time.time() + 1.0

        parla_sintesi = False


# =========================
# RISPOSTA VOCALE
# =========================
def rispondi_e_parla(messaggio):

    print(botname + ": " + messaggio)
    speak(messaggio)
