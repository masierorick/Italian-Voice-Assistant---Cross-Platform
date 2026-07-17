import csv
import sys
import shutil
import subprocess
from threading import Thread
from modules.config import *
from modules.tts import speak


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
            subprocess.Popen([sys.executable, "-c", f"from modules.assistente import notes; notes({repr(testo)})"])


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

    #modifica per eseguire in un thread la radio e alleggerire il programma
    def start_radio():
        subprocess.Popen(["ffplay", "-nodisp", "-loglevel", "panic", url],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

    Thread(target=start_radio, daemon=True).start()

