#Assistente vocale con python in italiano
#2025 - Masiero Riccardo - tecnomas.engineering@gmail.com

#Librerie python necessarie per il funzionamento

#pip install gtts
#pip install playsound
#sudo apt install portaudio19-dev
#pip install speechrecognition
#pip install pyproject.toml
#pip install PyAudio
#pip install python-dotenv
#pip install google-api-python-client
#pip install rapidfuzz
#librerie per modalita' offline (STT/TTS senza connessione)
#pip install pywhispercpp
#pip install faster-whisper opzionale
#pip install piper-tts
#Piper richiede anche il binario "piper" nel PATH (o indicato via ASSISTENTE_PIPER_BIN)
#e un modello vocale .onnx + .onnx.json (es. it_IT-riccardo-x_low)
#Whisper richiede un modello (auto-scaricato al primo utilizzo, oppure indicato via ASSISTENTE_WHISPER_MODEL)

#gruppi AI da installare
#pip install groq
#pip install google-generativeai
#On UNIX, run the command below in the terminal
#export GROQ_API_KEY=real api key

import os
import re
import time
import random
import shutil
import signal
import json
import csv
import sys
import platform
import webbrowser
import threading
from threading import Thread
import subprocess
from multiprocessing import Process
from pathlib import Path
from gtts import gTTS
from playsound import playsound
from dotenv import load_dotenv
import speech_recognition as sr
import socket
import io
import PySide6
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject,Slot,Signal,QTimer
#AI importate
from groq import Groq
#from openai import OpenAI
from googleapiclient.discovery import build #serve per youtube api
from modules.config import *
from modules.ai import *
from modules.vocalrecon import *
from modules.intent import *
from modules.tts import *
from modules.network import ONLINE_MODE
from modules.radio import *
from modules.system import *


#Per Windows

if platform.system() == "Windows":

   # Aggiunge manualmente la directory di PySide6 dove ci sono tutte le DLL
   os.add_dll_directory(PySide6.__path__[0])

   # Imposta anche i percorsi QML
   os.environ["QML2_IMPORT_PATH"] = os.path.join(PySide6.__path__[0], "qml")
   os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(PySide6.__path__[0], "plugins", "platforms")

# Imposta la variabile di ambiente QT_QPA_PLATFORM su Linux
if platform.system() == "Linux":
  os.environ["QT_QPA_PLATFORM"] = "xcb"



def load_state():
    default = {"attivo": False, "pid2": 0, "note_pids": []}
    if not STATE_FILE.exists():
        return default
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default



def save_state(state):
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    tmp.replace(STATE_FILE)



def downtime_control():
   #Controlla l'inattività dell'assistente.
   global attivo,time_start,sleep_time

   if attivo and time.perf_counter() - time_start >= sleep_time:

        #ripristino di tutte le variabili alla condizone iniziale
        attivo = False
        uscita = False
        riavvia = False
        scrivistatus()
        print(f"{botname} in stand-by.")



def scrivistatus():
    global attivo

    # === Salva il PID del processo nel JSON ===
    state = load_state()
    state["attivo"] = attivo
    save_state(state)



def estraipid(pid2):

  pattern = r'(\w+)\s*=\s*(.*)'  #\w+ corrisponde alla variabile, .* al valore dopo '='
  with open(STATE_FILE, 'r') as file:
    for numero_riga, riga in enumerate(file, 1):
       match = re.match(pattern, riga.strip())  # Cerca la corrispondenza
       if match:
            variabile = match.group(1)  # Variabile (prima del '=')
            if "pid2" in variabile:
              pid2 = int(match.group(2))  # Valore (dopo '=')





# =============================================
# 🎤 FUNZIONE PRINCIPALE RICONOSCIMENTO COMANDO
# =============================================

#Riconoscimento vocale parametri iniziali
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8
recognizer.non_speaking_duration = 0.5

def comrecon(comando):
    global attivo, listreplybot, listsaluti, main_path, time_start, uscita, riavvia, youtubeopen, messaggio, parla_sintesi
    #attendi_conferma = True
    listaprogrammi = main_path / "data/listaprogrammi"
    listabookmarks = main_path / "data/bookmarks"
    pid2 = 0
    comando = comando.lower().strip()
    comando = adattalingua(comando)
    scrivistatus()
    time_start = time.perf_counter()


    if not attivo:
        if re.search(rf"\b{wakeword}\b", comando):
            attivo = True
            scrivistatus()

            if comando.strip() == wakeword:
                rispondi_e_parla(random.choice(listreplybot))
            else:
                comando_pulito = re.sub(rf"\b{wakeword}\b", "", comando).strip()
                if not parla_sintesi:
                       print(messages["other_messages"]["command"].format(comando=comando_pulito))

                esegui(comando_pulito)
    else:
        # Rimuove wakeword anche quando già attivo
        comando_pulito = re.sub(rf"\b{wakeword}\b", "", comando).strip()
        if comando_pulito:
            if not parla_sintesi:
                print(messages["other_messages"]["command"].format(comando=comando_pulito))
            esegui(comando_pulito)
        else:
            rispondi_e_parla(random.choice(listreplybot))



class ProcessManager(QObject):

    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window

    @Slot()
    def close_window(self):
        """ Chiude la finestra associata """
        if self.app_window:
            self.app_window.close()

    @Slot(str)
    def check_text(self, testo):
        """ Controlla e aggiorna il testo nell'interfaccia QML """

        if self.app_window:
            text_obj = self.app_window.findChild(QObject, "testo")
            if text_obj:
                text_obj.setProperty("text", testo)
            else:
                print(messages["error_messages"]["error_object"].format(testo=testo))
        else:
            print(messages["error_messages"]["error_window"])




def notes(testo):
    """ Avvia l'applicazione QML e imposta il testo iniziale """
    global numnote  # Mantiene il conteggio delle note

    app = QGuiApplication(sys.argv)

    # Crea l'applicazione
    app.setOrganizationName("TecnoMas")
    app.setOrganizationDomain("tecnomas.engineering.com")
    app.setApplicationName("notes")

    # Configura il file QML e lo carica
    engine = QQmlApplicationEngine()
    engine.load(main_path / 'ui/notes.qml')

    if not engine.rootObjects():
        print(messages["error_messages"]["error_load_qml"])
        sys.exit(-1)

    root_object = engine.rootObjects()[0]

    # Crea l'istanza di ProcessManager e passa la finestra principale
    process_manager = ProcessManager(app_window=root_object)
    engine.rootContext().setContextProperty("processManager", process_manager)  # Collegamento alla classe in QML

    # Aggiorna il testo tramite il metodo check_text
    process_manager.check_text(testo)

    numnote += 1  # Incrementa il conteggio delle note

    # Salva il PID in un file
    with open(STATE_FILE, 'w') as f:
        f.write(f"note{numnote} = {os.getpid()}\n")

    app.exec()



class AnimationManager(QObject):
    newOutput = Signal(str)  # Segnale che invia l'output alla UI



    def __init__(self):
        super().__init__()
        self.window = None


    def write(self, text):
        if text.strip():
            self.newOutput.emit(text.strip())  # Invia il testo alla UI

    def flush(self):
        pass  # Necessario per compatibilità con sys.stdout

    @Slot(str)
    def sendCommand(self, command):
        global attivo
        """Riceve il comando dal QML ed esegue l'azione corrispondente."""
        try:
            attivo = True
            comrecon(command)  # Esegue comrecon senza aspettare un ritorno
        except Exception as e:
            self.newOutput.emit(messages["error_messages"]["called_process_error"].format(e=e))

    @Slot()  # Slot per chiusura finestre UI
    def stop_process(self):
        pid2 = 0
        QApplication.quit()  # Termina l'applicazione
        estraipid(pid2)
        os.kill(pid2, signal.SIGTERM)
        exit()

    @Slot()
    # Slot per controllo cambio colore botname nel caso sia attivo
    def checkColor(self):
        if not engine.rootObjects():
          return
        root_object = engine.rootObjects()[0]
        testo = root_object.findChild(QObject, "botname")

        if testo:
            color = "red" if attivo else "white"
            testo.setProperty("color", color)  # Modifica il colore

    @Slot()
    def loadWindow(self):
      global layout

      #imposta layout e scrive su file config.json
      if layout == "uniwindow":
        layout = "main"


      elif layout == "main":
        layout = "uniwindow"

      # Leggi il file JSON esistente
      try:
        with open(config_path, "r") as file:
            config = json.load(file)
      except (FileNotFoundError, json.JSONDecodeError):
            config = {}  # Se il file non esiste o è vuoto, inizia con un dizionario vuoto

      # Modifica solo il valore della chiave "layout"
      config["layout"] = layout

      # Scrivere i dati nel file config.json
      with open(config_path, "w") as file:
            json.dump(config, file, indent=4)

      if self.window:
        self.window.deleteLater()  # Chiude la finestra attuale
        self.window = None

      # Aspetta la fine del ciclo di eventi prima di riavviare l'app
      QTimer.singleShot(0, self.restart_application)

      #self.restart_application()

    def restart_application(self):
         # Riavvia l'applicazione tramite subprocess
         try:
            subprocess.Popen([sys.executable] + sys.argv)  # Riavvia lo script corrente
         except Exception as e:
              print(messages["error_messages"]["error_reboot"].format(e=e))

         QApplication.exit(0)  # Chiude l'istanza attuale in modo sicuro
         # Esci immediatamente, poiché l'applicazione è stata riavviata
         sys.exit(0)


def avvia_interfaccia(app_name, qml_files):
    global engine

    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # Parametri importanti per salvare il file delle impostazioni
    app.setOrganizationName("TecnoMas")
    app.setOrganizationDomain("tecnomas.engineering.com")
    app.setApplicationName(app_name)

    # Leggere il file JSON in Python
    with open(config_path, "r") as file:
        config_data = json.load(file)

    # Crea l'istanza di animationManager e passa la finestra principale
    animationManager = AnimationManager()
    sys.stdout = animationManager  # Reindirizza stdout alla nostra classe
    engine.rootContext().setContextProperty("animationManager", animationManager)
    engine.rootContext().setContextProperty("configData", config_data)
    engine.quit.connect(app.quit)

    # Carica i file QML specificati
    for qml_file in qml_files:
        engine.load(main_path / qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    app.exec()

def uniwindow():
    avvia_interfaccia("uniwindow", ['ui/uniwindow.qml'])


def animazione():
    avvia_interfaccia("assistente", ['ui/main.qml', 'ui/listcom.qml'])



#===============================
#ROUTINE PRINCIPALE DI ASCOLTO
#===============================


def listen():
    """Ciclo principale di ascolto."""
    global time_start,parla_sintesi,layout,musicprog

    #determinazione layoutgrafico
    if layout == "main":
        grafica = animazione
    else:
        grafica = uniwindow

    #controllo player mp3 di default
    musicprog = get_default_mp3_app()
    config["musicplayer"] = musicprog

    #scrittura nel file config.json del player mp3 di default
    with open(config_path, "w") as file:
            json.dump(config, file, indent=4)

    if (ONLINE_MODE):
        tts_mode = "Google"
        stt_mode = "Google"

    else :
        tts_mode = "Piper OffLine"
        stt_mode = "Whisper Offline"

    with sr.Microphone() as source:
       recognizer.adjust_for_ambient_noise(source, duration=1)
       #avvio interfaccia grafica
       Thread(target=grafica,daemon=True).start()
       time.sleep(1)
       print (f"🎙️ Riconoscimento vocale: {stt_mode}")
       print (f"🔊 Sintesi vocale: {tts_mode}")
       print(messages["other_messages"]["waiting_wakeword"].format(botname=botname))

       while True:
            try:
                if parla_sintesi:
                         time.sleep(0.1)
                         continue
                #thread  per controllo periodico stato  assistente lasciare in questa posizione evita di dover fare il loop
                Thread(target=downtime_control, daemon=True).start()

                #Sequenza senza uso di thread
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)

                if ONLINE_MODE:
                    try:

                        comando = recognizer.recognize_google(audio, language="it-IT,en-US").lower()
                    except sr.RequestError as e:
                        print(f"[STT] Google STT non raggiungibile ({e}), passo a whisper offline.")
                        comando = trascrivi_offline(audio).lower()
                else:

                    comando = trascrivi_offline(audio).lower()

                if not comando:
                    continue

                comrecon(comando)

            except sr.UnknownValueError:
               pass
            except sr.RequestError:
               pass
            except sr.WaitTimeoutError:
               pass





