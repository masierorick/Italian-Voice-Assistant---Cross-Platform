import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# =========================
# PATH & CONFIG
# =========================
main_path = Path.cwd()
current_dir = os.path.dirname(os.path.abspath(__file__))
radios_csv = main_path / "data/stations.csv"
config_path = main_path / "config/config.json"
messages_path = main_path / "config/messages_it.json"
STATE_FILE = main_path / "data" / "state.json"

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

#Sequenze di risposta
# Assegna i messaggi alle variabili
listreplybot = messages["welcome_messages"]
listsaluti = messages["goodbye_messages"]
error_file_not_found = messages["error_messages"]["file_not_found"]
radio_list_message = messages["other_messages"]["radio_list"]


attivo = False
uscita = False
riavvia = False
time_start = 0
parla_sintesi = False # Flag per controllare lo stato della sintesi vocale
numnote= 0
youtubeopen = False
messaggio = ""
engine = None
