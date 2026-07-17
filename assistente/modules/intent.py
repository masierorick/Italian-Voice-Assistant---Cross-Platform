import os
import sys
import signal
import random
import subprocess
import platform
import webbrowser
import re
from pathlib import Path
from modules.tts import *
from modules.radio import *
from modules.config import (
    messages,
    main_path,
    listsaluti,
    uscita,
    riavvia,
    parla_sintesi
)

from modules.ai import *
from modules.system import *

# =========================
# ESEGUI INTENTI
# =========================

def esegui_intent(intent, comando):
    global listsaluti, main_path, uscita, riavvia, youtubeopen, pid2,parla_sintesi
    listaprogrammi = main_path / "data/listaprogrammi"
    listabookmarks = main_path / "data/bookmarks"
    pid2 = 0, 0
    sistema = platform.system().lower()

    # Normalizzazione del comando
    comando = comando.lower().strip()



    # =====================
    # CONFERME
    # =====================
    if intent == "confirm":
        if "no" in comando:
            uscita = False
            riavvia = False
            rispondi_e_parla(messages["other_messages"]["shutdown_cancelled"])
            return

        if contiene_parola(comando, messages["commands"]["reply"]):

            if uscita:
                rispondi_e_parla(random.choice(messages["other_messages"]["shutdown_executed"]))
                rispondi_e_parla(random.choice(listsaluti))
                if sistema == "linux":
                    os.system("shutdown -h now")
                elif sistema == "windows":
                    os.system("shutdown /s /f /t 0")
                elif sistema == "darwin":  # macOS
                    os.system("sudo shutdown -h now")



            elif riavvia:
                rispondi_e_parla(messages["other_messages"]["reboot_executed"])
                if sistema == "linux":
                    os.system("reboot")
                elif sistema == "windows":
                    os.system("shutdown /r /f /t 0")
                elif sistema == "darwin":  # macOS
                    os.system("sudo shutdown -r now")
                else:
                    rispondi_e_parla(messages["other_messages"]["reboot_failed"])

        return "done"

    # =====================
    # RADIO
    # =====================
    if intent == "radio_list":
        rispondi_e_parla(messages["other_messages"]["radio_list"])
        lista_radio_csv()

    elif intent == "radio_gui":
        rispondi_e_parla("Apro PyRadio")
        subprocess.Popen(["pyradio"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif intent == "radio_change":
        subprocess.run(["pkill", "ffplay"])
        ricerca_stazione_csv(comando)

    elif intent == "radio_off":
        rispondi_e_parla(messages["other_messages"]["radio_closed"])
        subprocess.run(["pkill", "ffplay"])

    elif intent == "radio_volume":
        setVolume(comando)

    # =====================
    # SISTEMA
    # =====================
    elif intent == "shutdown":
        rispondi_e_parla(messages["other_messages"]["command_confirmation"])
        uscita = True

    elif intent == "reboot":
        rispondi_e_parla(messages["other_messages"]["command_confirmation"])
        riavvia = True

    elif intent == "update":
        aggiorna_sistema()

    # =====================
    # CHIUSURA ASSISTENTE
    # =====================
    elif intent == "assistant_exit":
        rispondi_e_parla(random.choice(listsaluti))
        estraipid(pid2)
        os.kill(pid2, signal.SIGTERM)
        exit()

    # =====================
    # VOLUME
    # =====================
    elif intent == "volume":
        setVolume(comando)

    # =====================
    # OPEN
    # =====================
    elif intent == "open":
        if "gestore" in comando and "file" in comando:
            apri_gestore_file(".")
        elif not apriBookmarks(listabookmarks, comando):
            apriProgrammi(listaprogrammi, comando)
               # return "fallback_ai"

    # =====================
    # CLOSE
    # =====================
    elif intent == "close":
        chiudiProgrammi(listaprogrammi, comando)

    # =====================
    # SEARCH
    # =====================
    elif intent == "search":
        if "youtube" in comando or youtubeopen:
            risultati = cerca_youtube(comando, max_risultati=5)
            for url in risultati:
                webbrowser.open(url)
        else:
          return "fallback_ai"

    # =====================
    # AI DIRETTA
    # =====================
    elif intent == "ai_direct":
        response = get_groq_response(comando)
        subprocess.Popen([
            sys.executable,
            "-c",f"from modules.assistente import notes; notes({repr(response)})"
        ])

    #elif intent == "unknown":
    #return "fallback_ai"

    return "done"

# =========================
# 🚀 ESECUZIONE
# =========================

def esegui(comando):
    intent = riconosci_intent(comando)

    risultato = esegui_intent(intent, comando)

    if risultato == "fallback_ai":
        fallback_ai(comando)


# =========================
# 🤖 FALLBACK IA
# =========================

def fallback_ai(comando):
    response = get_groq_response(comando)

    subprocess.Popen([
        sys.executable,
        "-c",
        f"from modules.assistente import notes; notes({repr(response)})"
    ])

    url = estrai_url_da_rispostaIA(response)
    if url:
        webbrowser.open(url)


# =========================
#  RICONOSCIMENTO INTENT
# =========================

def riconosci_intent(comando):
    # PRIORITÀ: conferme
    if uscita or riavvia:
        return "confirm"

    # RADIO
    if re.search(r"\bradio\b", comando):
        if contiene_parola(comando, messages["objects"]["list"]):
            return "radio_list"
        if contiene_parola(comando, messages["objects"]["graphic"]):
            return "radio_gui"
        if contiene_parola(comando, messages["commands"]["turnoff"]):
            return "radio_off"
        if contiene_parola(comando, messages["commands"]["silent"]):
            return "radio_volume"
        if contiene_parola(comando, messages["commands"]["change"] + messages["commands"]["open"]):
            return "radio_change"
        return "radio_generic"

    # SISTEMA
    if contiene_parola(comando, messages["commands"]["turnoff"]) and contiene_parola(comando, messages["objects"]["pc"]):
        return "shutdown"

    if contiene_parola(comando, messages["commands"]["restart"]) and contiene_parola(comando, messages["objects"]["pc"]):
        return "reboot"

    if contiene_parola(comando, messages["commands"]["update"]) and contiene_parola(comando, messages["objects"]["pc"]):
        return "update"

    # CHIUSURA ASSISTENTE
    if (
        contiene_parola(comando, messages["commands"]["exit"] + ["chiuditi"])
        and contiene_parola(comando, messages["objects"]["program"])
    ):
        return "assistant_exit"

    # VOLUME
    if "volume" in comando:
        return "volume"

    # OPEN
    if contiene_parola(comando, messages["commands"]["open"]):
        return "open"

    # CLOSE
    if contiene_parola(comando, messages["commands"]["close"]):
        return "close"

    # SEARCH
    if contiene_parola(comando, messages["commands"]["search"]):
        return "search"

    # AI DIRETTA
    if contiene_parola(comando, messages["commands"]["getAI"]) and "youtube" not in comando:
        return "ai_direct"

    return "unknown"

def contiene_parola(comando, parole):
    return any(re.search(rf"\b{re.escape(p)}\b", comando) for p in parole)
