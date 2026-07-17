from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import shutil
import subprocess
import sys

# FUNZIONE PER LEGGERE requirements.txt
def read_requirements(file_path):
    """Legge requirements.txt filtrando commenti e linee vuote"""
    requirements = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-r'):
                requirements.append(line)
    return requirements

class PostInstallCommand(install):
    def run(self):
        install.run(self)
        user_home = os.path.expanduser("~")
        autostart_dir = os.path.join(user_home, ".config", "autostart")
        applications_dir = os.path.join(user_home, ".local", "share", "applications")

        source_file = os.path.join(os.path.dirname(__file__), "resources", "AI.desktop")
        icon_file = os.path.join(os.path.dirname(__file__), "resources", "icon.png")

        os.makedirs(autostart_dir, exist_ok=True)
        os.makedirs(applications_dir, exist_ok=True)

        with open(source_file, "r") as f:
            desktop_content = f.read()

        # Sostituisce segnaposto con la home dell’utente
        desktop_content = desktop_content.replace("{HOME}", user_home)

        # Copia icon.png nello stesso target_dir dove scrivi AI.desktop
        for target_dir in [autostart_dir, applications_dir]:
            #copia icona
            target_icon_file = os.path.join(target_dir, "icon.png")
            shutil.copy(icon_file, target_icon_file)

            #Scrive il file desktop agiornato
            target_file = os.path.join(target_dir, "AI.desktop")
            with open(target_file, "w") as f:
                f.write(desktop_content)

        print("File .desktop installati con successo!")

def install_portaudio():
    """Installa automaticamente PortAudio prima di installare i pacchetti Python"""
    try:
        if sys.platform.startswith("linux"):
            subprocess.run(["sudo", "apt", "install", "-y", "portaudio19-dev"], check=True)
        elif sys.platform == "darwin":
            subprocess.run(["brew", "install", "portaudio"], check=True)
        elif sys.platform == "win32":
            print("⚠️ Su Windows, installa PortAudio manualmente")
    except Exception as e:
        print(f"Errore PortAudio: {e}")


# Installare PortAudio prima di procedere con l'installazione delle dipendenze Python
install_portaudio()

setup(
    name="Assistente",
    version="3.0",
    author="Masiero Riccardo",
    author_email="tecnomas.engneering@gmail.com",
    description="assistente vocale in italiano",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tuo_account/my_project",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "assistente": [
            "ui/*.gif",
            "ui/*.qml",
            "ui/*.png",
            "data/*.*",
            "data/*.csv",
            #"script/.env",
            "config/*.json",
            "resources/*.png",
            "resources/*.desktop"
        ],
    },
    # USA requirements.txt automaticamente per risolvere automaticamente le dipendenze
    install_requires=read_requirements('requirements.txt'),

    cmdclass={'install': PostInstallCommand},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL v3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
)
