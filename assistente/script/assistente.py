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
import PySide6
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject,Slot,Signal,QTimer
#AI importate
from groq import Groq
from openai import OpenAI
from googleapiclient.discovery import build #serve per youtube api
from ddgs import DDGS #effettua ricerche di indirizzi tramite duckduckgo


load_dotenv()


#Percorsi principali
main_path = Path.cwd()
current_dir = os.path.dirname(os.path.abspath(__file__))
radios_csv = main_path / "data/stations.csv"
config_path = main_path / "config/config.json"
messages_path = main_path / "config/messages_it.json"


# Carica configurazione da file json
with open(config_path, "r") as config_file:
    config = json.load(config_file)

# Carica i messaggi dal file JSON
with open(messages_path, "r", encoding="utf-8") as f:
    messages = json.load(f)

#variabili globali di configurazione da cercare esternamente nel file config.json
botname = config["botname"]
wakeword = config["wakeword"]
sleep_time = config["sleep_time"]#  secondi per inattività
deltavolume = config["deltavolume"] #valore percentuale
layout = config["layout"]
musicprog = config["musicplayer"] #imposta il player di default
browser = config["browser"]

attivo = False
uscita = False
riavvia = False
time_start = 0
parla_sintesi = False # Flag per controllare lo stato della sintesi vocale
numnote= 0
youtubeopen = False
messaggio = ""
engine = None


#Sequenze di risposta
# Assegna i messaggi alle variabili
listreplybot = messages["welcome_messages"]
listsaluti = messages["goodbye_messages"]
error_file_not_found = messages["error_messages"]["file_not_found"]
radio_list_message = messages["other_messages"]["radio_list"]


#Riconoscimento vocale parametri iniziali
recognizer = sr.Recognizer()
#sensibilità microfono fissa (es. 300) o dinamica
#recognizer.energy_threshold = 180
#recognizer.dynamic_energy_threshold = 'True'
#recognizer.pause_threshold = 1.2

recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8
recognizer.non_speaking_duration = 0.5

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

# Configura la chiave API e il servizio
api_key_youtube = os.getenv("API_KEY_YOUTUBE") #legge api key di youtube dal file .env
youtube = build("youtube", "v3", developerKey=api_key_youtube)

#Groq API
clientGroq = Groq(api_key=os.getenv("API_KEY"))


def get_groq_response(text):
    """Funzione per ottenere risposta da Groq AI."""
    italian_prompt = f"Rispondi in italiano.\nTesto dell'utente: {text}"
    response = clientGroq.chat.completions.create(
        #model = "llama-3.1-8b-instant",
        model = "openai/gpt-oss-120b",
        messages=[{"role": "user", "content": italian_prompt}]
    )
    return response.choices[0].message.content

def estrai_url_da_rispostaIA(risposta):
    # Se è un dizionario, estrai la parte con l'URL
    if isinstance(risposta, dict):
        testo = risposta.get("text", "")
    else:
        testo = str(risposta)

    # Cerca il primo URL nella risposta
    match = re.search(r'https?://[^\s]+', testo)
    print(match)
    return match.group(0) if match else None


def cerca_youtube(query, max_risultati=5):
    try:
        # Rimuovi le parole non necessarie (esempio: "cerca su youtube")
        query_pulita = re.sub(r'cerca su youtube', '', query, flags=re.IGNORECASE).strip()
        print ("query_pulita:",query_pulita)

        if not query_pulita:
            print("Nessuna query valida dopo la pulizia.")
            return []

        # Cerca video su YouTube con la query pulita
        richiesta = youtube.search().list(
            q=query_pulita,
            part="snippet",
            type="video",
            maxResults=max_risultati
        )
        risposta = richiesta.execute()

        # Controllo se la risposta contiene "items"
        if "items" not in risposta:
            print("Nessun risultato trovato.")
            return []

        # Mostra i risultati
        urls= []
        for item in risposta["items"]:
            titolo = item["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            urls.append(url)  # Aggiungi ogni URL alla lista
            print(f"Titolo: {titolo}")
            print(f"URL: {url}")
            print("-" * 40)

        return urls

    except Exception as e:
        print(messages["error_messages"]["error_search_youtube"].format(e=e))
        return []


def speak(text):
    global parla_sintesi

    parla_sintesi = True
    tts = gTTS(text=text, lang='it')
    tts.save("response.mp3")
    playsound("response.mp3")
    os.remove("response.mp3")
    parla_sintesi = False


def downtime_control():
   #Controlla l'inattività dell'assistente.
   global attivo,time_start,sleep_time

   if attivo and time.perf_counter() - time_start >= sleep_time:

        attivo = False
        #ripristino di tutte le variabili alla condizone iniziale
        attivo = False
        uscita = False
        riavvia = False
        scrivistatus()
        print(f"{botname} in stand-by.")



def lista_radio_csv():
   """Stampa e visualizza la lista delle stazioni radio salvate."""
   try:
        with open(radios_csv, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            testo = radio_list_message + "\n"
            for line_count, row in enumerate(reader):
                if line_count > 0:
                    testo += f"{row[0]}\n"

            # Avvia la finestra delle note in un nuovo processo
            subprocess.Popen([sys.executable, "-c", f"from script.assistente import notes; notes({repr(testo)})"])


   except FileNotFoundError:
        print(messages["error_messages"]["error_file_not_found"])



def ricerca_stazione_csv(comando):
    """Ricerca una stazione radio e la avvia."""
    try:
        with open(radios_csv, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for line_count, row in enumerate(reader):
                if line_count > 0 and row[0].lower() in comando.lower():
                    play_radio_csv(row[0], row[1])
                    speak("Apro la radio.")
                    return
    except FileNotFoundError:
       print(messages["error_messages"]["error_file_not_found"])



def play_radio_csv(stazione,url):
    """Avvia una stazione radio."""
    if not shutil.which("ffplay"):
        speak("Installa ffmpeg per riprodurre la radio.")
        return
    print(messages["other_messages"]["radio_run"].format(stazione=stazione))
    #os.system(f"ffplay -nodisp -loglevel panic {url} &")
    #modifica per eseguire in un thread la radio e alleggerire il programma
    def start_radio():
        subprocess.Popen(["ffplay", "-nodisp", "-loglevel", "panic", url],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

    Thread(target=start_radio, daemon=True).start()



def apriBookmarks(listabookmarks, comando):
    global youtubeopen

    if "youtube" in comando:
        youtubeopen = True
    try:
        with open(listabookmarks, "r") as file:
            for line in file:
                # Rimuovi spazi e linee vuote
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Dividi la riga in chiave e valore
                if "=" in line:
                    bookmark, url = line.split("=", 1)
                    if bookmark.lower() in comando.lower():
                        # Esegui apertura browser all'url trovato
                        #webbrowser.open(url, new=2)
                        # uso thread per evitare overhead e velocizzare l'esecuzione senza complicazioni.
                        Thread(target=webbrowser.open, args=(url, 2), daemon=True).start()
                        speak("Pagina di " + bookmark.lower() + " aperta")
                        return True  # Azione completata, esci dalla funzione
    except FileNotFoundError:
        pass
    return False



def apri_gestore_file(percorso="."):
    # Apre il gestore file predefinito - già reso cross-platform

    try:
        if sys.platform.startswith("win"):  # Windows
            os.startfile(os.path.abspath(percorso))
        elif sys.platform.startswith("darwin"):  # macOS
            subprocess.run(["open", percorso], check=True)
        elif sys.platform.startswith("linux"):  # Linux e varianti
            # Prova diversi file manager popolari
            file_managers = ["xdg-open", "nautilus", "dolphin", "thunar", "pcmanfm"]
            for fm in file_managers:
                if os.system(f"which {fm} > /dev/null 2>&1") == 0:
                    #comando originale
                    #os.system(f"{fm} {percorso}")
                    #comando alternativo
                    subprocess.run([fm, percorso], check=True)
                    break
            else:
                raise RuntimeError(messages["error_messages"]["file_manager_error"])
        else:
            raise RuntimeError(messages["error_messages"]["platform_error"].format(piattaforma=sys.platform))
    except Exception as e:
        print(messages["error_messages"]["filemanger_error"])


#gestione dei media players cross-platform
def get_default_mp3_app_linux():
    try:
        # Ottiene il file .desktop associato
        result = subprocess.run(
            ["xdg-mime", "query", "default", "audio/mpeg"],
            capture_output=True, text=True, check=True
        )
        desktop_file = result.stdout.strip()
        search_paths = [
            Path("/usr/share/applications"),
            Path("/usr/local/share/applications"),
            Path.home() / ".local/share/applications"
        ]
        for path in search_paths:
            desktop_path = path / desktop_file
            if desktop_path.exists():
                with open(desktop_path, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.startswith("Exec="):
                            exec_line = line[len("Exec="):].strip()
                            exec_parts = exec_line.split()
                            if exec_parts[0] == "env":
                                # Cerca il vero comando dopo 'env' e variabili d'ambiente
                                for part in exec_parts[1:]:
                                    if not '=' in part:
                                        return part
                                return "env"  # fallback
                            else:
                                return exec_parts[0]
        return desktop_file
    except Exception as e:
        return None



def get_default_mp3_app_macos():
    try:
        # Usa AppleScript per ottenere l'app predefinita per aprire mp3
        tmp_mp3 = "/tmp/test.mp3"
        if not os.path.exists(tmp_mp3):
            open(tmp_mp3, "wb").close()

        script = f'''
        set mp3file to POSIX file "{tmp_mp3}" as alias
        tell application "System Events"
            set defaultApp to name of application file of (open mp3file)
        end tell
        return defaultApp
        '''
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        app_name = result.stdout.strip()

        # Prova a recuperare percorso eseguibile tramite mdls
        app_paths = ["/Applications", str(Path.home() / "Applications")]
        for path in app_paths:
            candidate = os.path.join(path, app_name + ".app")
            if os.path.exists(candidate):
                return candidate  # percorso app macOS
        return app_name
    except Exception:
        return None


def get_default_mp3_app_windows():
    try:
        import winreg  # Import dinamico solo su Windows
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r".mp3") as key:
            progid, _ = winreg.QueryValueEx(key, None)
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, fr"{progid}\\shell\\open\\command") as key:
            command, _ = winreg.QueryValueEx(key, None)
        # command è tipo: "C:\\Program Files\\Windows Media Player\\wmplayer.exe" "%1"
        # Estrae solo il path eseguibile senza argomenti
        if command.startswith('"'):
            command = command.split('"')[1]
        else:
            command = command.split()[0]
        return command
    except Exception:
        return None

def get_default_mp3_app():
    system = platform.system()
    if system == "Linux":
        return get_default_mp3_app_linux()
    elif system == "Darwin":
        return get_default_mp3_app_macos()
    elif system == "Windows":
        return get_default_mp3_app_windows()
    return None


#fine gestione media player

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



def apriProgrammi(listaprogrammi, comando):
    global musicprog

    comandomod = adattalingua(comando)  # Funzione per adattare la lingua
    comando = comandomod

    # Caso speciale: apri il browser
    if any(word in comando for word in messages["objects"]["internet"]):
        # uso thread per evitare overhead e velocizzare l'esecuzione senza complicazioni.
        Thread(target=webbrowser.open, args=('www.google.it', 2), daemon=True).start()
        speak(messages["other_messages"]["browser_opened"])
        return True

    # Caso speciale: apri un'app musicale
    if any(word in comando for word in messages["objects"]["music"]):

        #if musicprog == "" or get_default_mp3_app() != musicprog : #disabilitato in modo che ogni volta esegua il controllo

        try:
            speak(messages["other_messages"]["music_player_opened"].format(musicprog=musicprog))
            os.system(musicprog+"&")  # Sostituisce os.system
            return True
        except FileNotFoundError:
            speak(messages["error_messages"]["program_not_found"])
            return False
        except subprocess.CalledProcessError as e:
            speak(messages["error_messages"]["called_process_error"])
            return False

    # Apri programmi da un file
    try:
        with open(listaprogrammi, "r") as file:
            for line in file:
                # Rimuovi spazi e linee vuote
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Dividi la riga in chiave e valore
                if "=" in line:
                    programma, comando_exe = line.split("=", 1)
                    if programma.lower() in comando.lower():
                        try:
                            # Esegui il programma usando subprocess.Popen
                            subprocess.Popen(comando_exe.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            speak(messages["other_messages"]["program_opened"].format(programma=programma))
                            return True
                        except FileNotFoundError:
                            speak(messages["error_messages"]["program_not_found"])
                            return False
                        except subprocess.CalledProcessError as e:
                            speak(messages["error_messages"]["called_process_error"])


                            return False
    except FileNotFoundError:
        speak(messages["error_messages"]["file_not_found"])
        return False




def chiudiProgrammi(listaprogrammi, comando):

    global youtubeopen,musicprog,browser

    trovato = False

    if any(word in comando for word in messages["objects"]["internet"]):
              youtubeopen = False
              os.system("pkill vivaldi-bin") #da vedere se inserire pkill {browser}
              speak(messages["other_messages"]["browser_closed"])
              return True
    if any(word in comando for word in messages["objects"]["music"]):
              os.system(f"pkill {musicprog}")
              speak(messages["other_messages"]["music_player_closed"])
              return True

    comandomod=adattalingua(comando)
    comando = comandomod


    try:
         with open(listaprogrammi, "r") as file:
            for line in file:
                # Rimuovi spazi e linee vuote
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Dividi la riga in chiave e valore
                if "=" in line:
                    programma, comando_exe = line.split("=", 1)
                    if programma.lower() in comando.lower():
                        # Esegui il comando dal sistema
                        comando = comando_exe
                        trovato = True

    except FileNotFoundError:
         speak(messages["error_messages"]["file_not_found"])
         return True

    if trovato:
      os.system("pkill " + comando)
      speak(messages["other_messages"]["program_closed"].format(programma=comando))



def scrivistatus():
    global attivo
    with open(current_dir + "/status.py", 'w') as f:
        f.write(f'attivo = {attivo}\n')  # Semplice, senza barre


def estraipid(pid2):

  pattern = r'(\w+)\s*=\s*(.*)'  #\w+ corrisponde alla variabile, .* al valore dopo '='
  with open(current_dir+"/pid.py", 'r') as file:
    for numero_riga, riga in enumerate(file, 1):
       match = re.match(pattern, riga.strip())  # Cerca la corrispondenza
       if match:
            variabile = match.group(1)  # Variabile (prima del '=')
            if "pid2" in variabile:
              pid2 = int(match.group(2))  # Valore (dopo '=')
              #print (variabile, pid2)



def setVolume(azione):
   #inserita funzione cross-platform
    global deltavolume

    if platform.system() == "Windows":
     try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
     except ImportError:
        print(messages["error_messages"]["program_not_found"].format(program="pycaw"))

    system_platform = platform.system()

    def extract_percentage(azione):
        digits = ''.join(filter(str.isdigit, azione))
        return int(digits) if digits else None

    if system_platform == "Linux":
        percent = extract_percentage(azione)
        if any(word in azione for word in messages["commands"]["setvol"]):
            if percent is not None:
                os.system("pactl set-sink-mute @DEFAULT_SINK@ 0")  # Unmute
                os.system(f"pactl set-sink-volume @DEFAULT_SINK@ {percent}%")
                print(messages["other_messages"]["volume_set"].format(percent=percent))
        elif any(word in azione for word in messages["commands"]["upvol"]):
            os.system("pactl set-sink-mute @DEFAULT_SINK@ 0")  # Unmute
            os.system(f"pactl set-sink-volume @DEFAULT_SINK@ +{deltavolume}%")
            print(messages["other_messages"]["volume_increased"].format(deltavolume=deltavolume))
        elif any(word in azione for word in messages["commands"]["downvol"]):
            os.system("pactl set-sink-mute @DEFAULT_SINK@ 0")  # Unmute
            os.system(f"pactl set-sink-volume @DEFAULT_SINK@ -{deltavolume}%")
            print(messages["other_messages"]["volume_decreased"].format(deltavolume=deltavolume))
        elif any(word in azione for word in messages["commands"]["silent"]):
            os.system("pactl set-sink-mute @DEFAULT_SINK@ toggle")
            print(messages["other_messages"]["volume_muted"])
        else:
            print(messages["error_messages"]["command_not_recognized"])

    elif system_platform == "Darwin":  # macOS
        percent = extract_percentage(azione)
        if any(word in azione for word in messages["commands"]["setvol"]):
            if percent is not None:
                os.system("osascript -e 'set volume output muted false'")  # Unmute
                os.system(f"osascript -e 'set volume output volume {percent}'")
                print(messages["other_messages"]["volume_set"].format(percent=percent))
        elif any(word in azione for word in messages["commands"]["upvol"]):
            os.system("osascript -e 'set volume output muted false'")  # Unmute
            os.system(f"osascript -e 'set volume output volume (output volume of (get volume settings) + {deltavolume})'")
            print(messages["other_messages"]["volume_increased"].format(deltavolume=deltavolume))
        elif any(word in azione for word in messages["commands"]["downvol"]):
            os.system("osascript -e 'set volume output muted false'")  # Unmute
            os.system(f"osascript -e 'set volume output volume (output volume of (get volume settings) - {deltavolume})'")
            print(messages["other_messages"]["volume_decreased"].format(deltavolume=deltavolume))
        elif any(word in azione for word in messages["commands"]["silent"]):
            os.system("osascript -e 'set volume output muted not (output muted of (get volume settings))'")
            print(messages["other_messages"]["volume_muted"])
        else:
            print(messages["error_messages"]["command_not_recognized"])

    elif system_platform == "Windows":
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            percent = extract_percentage(azione)
            if any(word in azione for word in messages["commands"]["setvol"]):
                if percent is not None:
                    volume.SetMute(0, None)  # Unmute
                    volume.SetMasterVolumeLevelScalar(percent / 100, None)
                    print(messages["other_messages"]["volume_set"].format(percent=percent))
            elif any(word in azione for word in messages["commands"]["upvol"]):
                volume.SetMute(0, None)  # Unmute
                volume.SetMasterVolumeLevelScalar(min(volume.GetMasterVolumeLevelScalar() + deltavolume / 100, 1.0), None)
                print(messages["other_messages"]["volume_increased"].format(deltavolume=deltavolume))
            elif any(word in azione for word in messages["commands"]["downvol"]):
                volume.SetMute(0, None)  # Unmute
                volume.SetMasterVolumeLevelScalar(max(volume.GetMasterVolumeLevelScalar() - deltavolume / 100, 0.0), None)
                print(messages["other_messages"]["volume_decreased"].format(deltavolume=deltavolume))
            elif any(word in azione for word in messages["commands"]["silent"]):
                volume.SetMute(not volume.GetMute(), None)
                print(messages["other_messages"]["volume_muted"])
            else:
                print(messages["error_messages"]["command_not_recognized"])
        except Exception as e:
            print(messages["error_messages"]["error_volume_control"].format(system=system_platform))
    else:
        print(messages["error_messages"]["error_system"])


def contiene_parola(comando, parole):
    return any(re.search(rf"\b{re.escape(p)}\b", comando) for p in parole)

def rispondi_e_parla(messaggio):
    print(botname + ": " + messaggio)
    speak(messaggio)

# =========================
#  INTENT RECOGNITION
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

# =========================
#  AGGIORNA SISTEMA
# =========================

def aggiorna_sistema():
    sistema = platform.system().lower()
    print(sistema)

    rispondi_e_parla(messages["other_messages"]["update_in_progress"])

    processi = []
    ambiente = ""

    try:
        if sistema == "linux":
            ambiente = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
            print(ambiente)

            if "kde" in ambiente:
                processi.append(subprocess.Popen(["sudo", "pkcon", "update", "-y"]))

            elif "gnome" in ambiente or "ubuntu" in ambiente:
                processi.append(subprocess.Popen(["sudo", "apt", "update"]))
                processi.append(subprocess.Popen(["sudo", "apt", "upgrade", "-y"]))

            elif "xfce" in ambiente:
                processi.append(subprocess.Popen(["sudo", "pacman", "-Syu", "--noconfirm"]))

            else:
                processi.append(subprocess.Popen(["sudo", "apt", "update"]))
                processi.append(subprocess.Popen(["sudo", "apt", "upgrade", "-y"]))

        elif sistema == "windows":
            try:
                processi.append(subprocess.Popen(["winget", "upgrade", "--all"]))
            except Exception:
                try:
                    processi.append(subprocess.Popen(["choco", "upgrade", "all", "-y"]))
                except Exception as e:
                    print(messages["error_messages"]["update_error"], e)

    except Exception as e:
        print("Errore update:", e)
        return

    def wait_updates():
        for p in processi:
            p.wait()

        rispondi_e_parla(messages["other_messages"]["update_completed"])

    threading.Thread(target=wait_updates, daemon=True).start()

# =========================
# ESEGUI INTENTI
# =========================

def esegui_intent(intent, comando):
    global listsaluti, main_path, uscita, riavvia, youtubeopen, pid2
    listaprogrammi = main_path / "data/listaprogrammi"
    listabookmarks = main_path / "data/bookmarks"
    pid1, pid2 = 0, 0
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
            if not apriProgrammi(listaprogrammi, comando):
                return "fallback_ai"

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

    # =====================
    # AI DIRETTA
    # =====================
    elif intent == "ai_direct":
        response = get_groq_response(comando)
        subprocess.Popen([
            sys.executable,
            "-c",
            f"from script.assistente import notes; notes({repr(response)})"
        ])

    elif intent == "unknown":
        return "fallback_ai"

    return "done"

# =========================
# 🤖 FALLBACK IA
# =========================

def fallback_ai(comando):
    response = get_groq_response(comando)
    url = estrai_url_da_rispostaIA(response)

    if url:
        webbrowser.open(url)
        #speak("Apro quello che ho trovato")
    #else:
        #speak("Non ho trovato nulla")

# =========================
# 🎤 FUNZIONE PRINCIPALE
# =========================

def comrecon(comando):
    global attivo, listreplybot, listsaluti, main_path, radios_json, time_start, uscita, riavvia,youtubeopen,messaggio,parla_sintesi
    attendi_conferma = True
    listaprogrammi = main_path / "data/listaprogrammi"
    listabookmarks = main_path / "data/bookmarks"
    pid1, pid2 = 0, 0
    risposte_comando = messages["commands"]["reply"]  #equivale al si ,certo,certamente
    sistema = platform.system().lower()

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
                esegui(comando)
    else:
        esegui(comando)

# =========================
# 🚀 ESECUZIONE
# =========================

def esegui(comando):
    intent = riconosci_intent(comando)

    risultato = esegui_intent(intent, comando)

    if risultato == "fallback_ai":
        fallback_ai(comando)



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
    with open(current_dir + "/notepid.py", 'w') as f:
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


def listen():
    """Ciclo principale di ascolto."""
    global time_start,parla_sintesi,layout,musicprog

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



    with sr.Microphone() as source:
       recognizer.adjust_for_ambient_noise(source, duration=1)
       Thread(target=grafica,daemon=True).start()
       time.sleep(1)
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
                comando = recognizer.recognize_google(audio,language="it-IT,en-US").lower()
                comrecon(comando)

            except sr.UnknownValueError:
               pass
            except sr.RequestError:
               pass
            except sr.WaitTimeoutError:
               pass





