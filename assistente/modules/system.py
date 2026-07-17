import os
import sys
import csv
import shutil
import platform
import subprocess
import threading
import webbrowser

from pathlib import Path
from threading import Thread


from modules.config import (
    radios_csv,
    messages,
    radio_list_message,
    musicprog,
    browser,
    deltavolume,
)

from modules.tts import speak, rispondi_e_parla
from modules.vocalrecon import adattalingua

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
                        rispondi_e_parla("Pagina di " + bookmark.lower() + " aperta")
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



# ==============================
# MEDIA PLAYERS CROSS-PLATFORMS
# ==============================
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




def apriProgrammi(listaprogrammi, comando):
    global musicprog

    #Funzione per adattare la lingua
    comando = adattalingua(comando)

    # Caso speciale: apri il browser
    if any(word in comando for word in messages["objects"]["internet"]):
        # uso thread per evitare overhead e velocizzare l'esecuzione senza complicazioni.
        Thread(target=webbrowser.open, args=('www.google.it', 2), daemon=True).start()
        rispondi_e_parla(messages["other_messages"]["browser_opened"])
        return True

    # Caso speciale: apri un'app musicale
    if any(word in comando for word in messages["objects"]["music"]):

        #if musicprog == "" or get_default_mp3_app() != musicprog : #disabilitato in modo che ogni volta esegua il controllo

        try:
            rispondi_e_parla(messages["other_messages"]["music_player_opened"].format(musicprog=musicprog))
            os.system(musicprog+"&")  # Sostituisce os.system
            return True
        except FileNotFoundError:
            rispondi_e_parla(messages["error_messages"]["program_not_found"])
            return False
        except subprocess.CalledProcessError as e:
            rispondi_e_parla(messages["error_messages"]["called_process_error"])
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
                            rispondi_e_parla(messages["other_messages"]["program_opened"].format(programma=programma))
                            return True
                        except FileNotFoundError:
                            rispondi_e_parla(messages["error_messages"]["program_not_found"])
                            return False
                        except subprocess.CalledProcessError as e:
                            rispondi_e_parla(messages["error_messages"]["called_process_error"])


                            return False
    except FileNotFoundError:
        rispondi_e_parla(messages["error_messages"]["file_not_found"])
        return False




def chiudiProgrammi(listaprogrammi, comando):

    global youtubeopen,musicprog,browser

    trovato = False

    if any(word in comando for word in messages["objects"]["internet"]):
              youtubeopen = False
              os.system("pkill vivaldi-bin") #da vedere se inserire pkill {browser}
              rispondi_e_parla(messages["other_messages"]["browser_closed"])
              return True
    if any(word in comando for word in messages["objects"]["music"]):
              os.system(f"pkill {musicprog}")
              rispondi_e_parla(messages["other_messages"]["music_player_closed"])
              return True


    comando = adattalingua(comando)


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
         rispondi_e_parla(messages["error_messages"]["file_not_found"])
         return True

    if trovato:
      os.system("pkill " + comando)
      rispondi_e_parla(messages["other_messages"]["program_closed"].format(programma=comando))





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


# =================================
#  AGGIORNA SISTEMA CROSS-PLATFORM
# =================================

def aggiorna_sistema():
    sistema = platform.system().lower()
    rispondi_e_parla(messages["other_messages"]["update_in_progress"])

    processi = []

    try:
        if sistema == "linux":
            ambiente = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
            print(f"Desktop: {ambiente}")

            # Suggerimento dal desktop, ma shutil.which decide davvero
            if "kde" in ambiente and shutil.which("pkcon"):
                processi.append(subprocess.Popen(["sudo", "pkcon", "update", "-y"]))

            elif "kde" in ambiente and shutil.which("pacman"):
                processi.append(subprocess.Popen(["sudo", "pacman", "-Syu", "--noconfirm"]))

            elif any(d in ambiente for d in ["gnome", "ubuntu", "xfce"]) and shutil.which("apt"):
                processi.append(subprocess.Popen(["sudo", "apt", "update"]))
                processi.append(subprocess.Popen(["sudo", "apt", "upgrade", "-y"]))

            elif any(d in ambiente for d in ["gnome", "xfce"]) and shutil.which("pacman"):
                processi.append(subprocess.Popen(["sudo", "pacman", "-Syu", "--noconfirm"]))

            elif any(d in ambiente for d in ["gnome", "xfce"]) and shutil.which("dnf"):
                processi.append(subprocess.Popen(["sudo", "dnf", "upgrade", "-y"]))

            # Fallback: ignora il desktop, usa il primo gestore trovato
            elif shutil.which("apt"):
                processi.append(subprocess.Popen(["sudo", "apt", "update"]))
                processi.append(subprocess.Popen(["sudo", "apt", "upgrade", "-y"]))
            elif shutil.which("pacman"):
                processi.append(subprocess.Popen(["sudo", "pacman", "-Syu", "--noconfirm"]))
            elif shutil.which("dnf"):
                processi.append(subprocess.Popen(["sudo", "dnf", "upgrade", "-y"]))
            elif shutil.which("zypper"):
                processi.append(subprocess.Popen(["sudo", "zypper", "update", "-y"]))
            else:
                rispondi_e_parla("Gestore pacchetti non riconosciuto.")
                return

        elif sistema == "windows":
            if shutil.which("winget"):
                processi.append(subprocess.Popen(["winget", "upgrade", "--all"]))
            elif shutil.which("choco"):
                processi.append(subprocess.Popen(["choco", "upgrade", "all", "-y"]))
            else:
                rispondi_e_parla("Nessun gestore pacchetti trovato.")
                return

        elif sistema == "darwin":
            if shutil.which("brew"):
                processi.append(subprocess.Popen(["brew", "update"]))
                processi.append(subprocess.Popen(["brew", "upgrade"]))
            else:
                rispondi_e_parla("Homebrew non trovato.")
                return

    except Exception as e:
        print(messages["error_messages"]["update_error"], e)
        return

    def wait_updates():
        for p in processi:
            p.wait()
        rispondi_e_parla(messages["other_messages"]["update_completed"])

    threading.Thread(target=wait_updates, daemon=True).start()



