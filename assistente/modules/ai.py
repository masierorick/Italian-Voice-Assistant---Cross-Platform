
import os
import re

from dotenv import load_dotenv
from groq import Groq
from googleapiclient.discovery import build

from modules.config import messages

load_dotenv()

# =========================
# GROQ
# =========================
clientGroq = Groq(api_key=os.getenv("API_KEY_GROQ"))


def get_groq_response(text):
    """Funzione per ottenere risposta da Groq AI."""
    italian_prompt = f"Rispondi in italiano.\nTesto dell'utente: {text}"
    response = clientGroq.chat.completions.create(
        #model = "llama-3.1-8b-instant",
        #model = "openai/gpt-oss-120b",
        model="llama-3.3-70b-versatile",
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
