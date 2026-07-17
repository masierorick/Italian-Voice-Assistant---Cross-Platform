import csv
import sys
import shutil
import subprocess
import queue
import threading
from modules.config import *
from modules.tts import speak

radio_process = None
radio_reference = None
ffmpeg_process = None
radio_running = False


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



def play_radio_csv(stazione, url):
    """Avvia una stazione radio."""

    global radio_process, radio_reference

    if not shutil.which("ffmpeg"):
        speak("Installa ffmpeg per riprodurre la radio.")
        return

    print(messages["other_messages"]["radio_run"].format(stazione=stazione))

    def start_radio():

        global radio_process, radio_reference

        audio_queue = queue.Queue(maxsize=50)
        global ffmpeg_process
        ffmpeg_process = subprocess.Popen(["ffmpeg", "-i", url, "-f", "s16le", "-ar", "48000", "-ac", "2", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        def read_audio(ffmpeg):
            while True:
                data = ffmpeg.stdout.read(4096)

                if not data:
                    break

                try:
                    audio_queue.put(data, timeout=1)
                except queue.Full:
                    pass

        threading.Thread(target=read_audio, args=(ffmpeg_process,), daemon=True).start()

        class RadioReference:
            def read(self, size):
                try:
                    return audio_queue.get(timeout=1)
                except queue.Empty:
                    return b""

        radio_reference = RadioReference()

        from modules.audio_filter import set_radio_reference
        set_radio_reference(radio_reference)
        global radio_process
        radio_process = subprocess.Popen(["ffplay", "-nodisp", "-loglevel", "panic", "-f", "s16le", "-ar", "48000", "-ac", "2", "-"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        while True:
            data = audio_queue.get()

            if not data:
                 break

            try:
              if radio_process.poll() is not None:
                break

              radio_process.stdin.write(data)
              radio_process.stdin.flush()

            except (BrokenPipeError, OSError):
               break

    threading.Thread(target=start_radio, daemon=True).start()

def stop_radio():

    global radio_process, ffmpeg_process, radio_running

    radio_running = False

    if radio_process:
        try:
            radio_process.terminate()
        except:
            pass
        radio_process = None

    if ffmpeg_process:
        try:
            ffmpeg_process.terminate()
        except:
            pass
        ffmpeg_process = None
