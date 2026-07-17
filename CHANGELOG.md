# Changelog
# [3.5.0] -2026-07-17 
- Diviso il programma assistente monolitico in diversi moduli e spostati tutti nella sottodirectory /modules
- eliminati i files notepid.py, pid.py e status.py che servivono solo per una variabile e importati tutte le variabile sotto un unico fil in /data/state.json e modificato il programma per leggerlo 
- inserito il comando rispondi e parla dove c'erà solo speak per visualizzare nella ui quanto detto dal botname 
- modificato il file main.py per avviare listan da /modules/assistente
- inserita la possibilità di eseguire il programma offline con whisper e piper 

# [3.4.0] -2026-05-06
- Riscritto codice assistente.py per renderlo più leggibile nelle chiamate di comando
- Risolto problema su chiamata funzione radio che mandava in loop la richiesta

# [3.2.3] -2026-02-12
-Inserito modello differente su ia groq . Disabilitato #model = "llama-3.1-8b-instant" e abilitato model = "openai/gpt-oss-120b"

# [3.2.2] -2025-08-25 
- Effettuate modifiche sulle routine di chiusura o uscite  del sistema inserendo prima il no del controllo dei pattern altrimenti il programma eseguuiva comunque il comando di chiusura o uscita indipendentemente da cosa veniva detto. 
- Inserita anche l normalizzazione del comando esci a volte mal interpretata dal riconoscimento vocale 

# [3.2.1.] -2025-06-19 
- Inserito nella routine principale di assistente lo script per verificare il programma mp3 di default prima dell'avvio di listen 

# [3.2.0] -2025-05-30 
- Modificato script per eseguire l'applicazionie musicale impostata di default 
- Adesso rileva automaticamente e cross-platform quale programma per eseguire file audio è impostato nel sistema .


# [3.1.0] -2025-05-15
- Inserito comando aggiornamento sistema cross - platfom 

# [3.0.2] -2025-04-26
- inserite correzioni per l'installazione e il funzionamento su windows 11

# [3.0.1] -2025-03-05 
- unificata la funzione di apertura delle 2 interfaccie su assistente.py 
- risolto errore apertura interfaccia differente con ritardo su avvio 2 interfaccia 
- sostituiti gli errori in italiano con la lista corrispondente su messages_it.json

## [3.0]  -2025-02-27
- creata versione assistente2 
- importato codice creazione ui assistente su assistente.py e risoluzione relativi problemi importazione (es. sostituito process con subrpocess.open in alcune funzioni)
- realizzata interfaccia ui uniwindow che integra ui main.qml con ui listcom.qml
- possibilità di switchare fra le 2 interfaccie 
- inserito a ui uniwindow.qml icona impostazioni per modifica layout 
- aggiunto a ui main.qml icona impostazioni con menù modifica layout 


## [2.5.7] -2025-02-27 
- Eliminato il downtime_control_loop che eseguiva thread continui e spostato il tread downtime_control in altra posizione 

## [2.5.6] -2025-02-26 
- Inserito nella lista dei comandi la possibilità di inviare anche messaggi testuali 
- corretti bug minori su errori 

## [2.5.5] -2025-02-18 
- Corrette le funzioni riavvia e esci che non lavoravano correttamente in uscita dal programma 

## [2.5.4] -2025-02-18
- Compattato il codice per riconoscimento dei comandi (la funzione esegui_com)
- Inserito il riconoscimento sia della lingua italiana che quella inglese 
- audio = recognizer.listen(source,timeout=10) eliminato phrase_time_limit=25 
- inserita nuova funzione adattalingua per errori di riconoscimento in inglese . Es. mito --> mitology

## [2.5.3] -2025-02-17
- Corretto gestione volume. In precedenza silenziando l'audio non era possibile riattivarlo.
- Inserito il comando "imposta il volume a " %

## [2.5.2] -2025-02-07
- Modificato lo schema di attivazione del programma . Adesso può essere eseguito il comando assieme alla wakeword.
- Risolto l'errore nelle finestre qml usando il comando import Qt.labs.settings 1.1. Basta sostituire con import QtCore.
- Aggiunto il comando per il passaggio diretto ad un altra stazione 

## [2.5.1] -2025-02-06
- reso cross-platform il comando volume
- Inserita deepseek come ai
- Risolto il problema sulla finestra notes.qml dove adessl la textarea permette la selezione del testo
- Rimossa Gemini AI in quanto a pagamento 

## [2.5.0] - 2025-01-30
- Risolto problematica confusione linguistica con si e sistema nella funzione comrecon
- Inserito azzeramento variabili riavvia,attivo e uscita nella funzione downtime_control
- inserimento file messages_it.json nella directory config per separare i messagi e i comandi in italiano

## [2.4.5]
- Inserita finestra qml con indicazione del log dei comandi recepiti
- inserita gemini come ai - ancora opzionale

## [2.4.0]
- inserita google api per ricerca su Youtube
- inserito ricerca variabili configurazione da esterno

## [2.3.0]
- Reso più compatto il codice con aggiunta di funzioni all'interno di comrecon
- aggiunto più risposte alla listreplybot e listsaluti
- corretto alcuni programmi che in italiano recepisce in modo diverso es. krita , konsole,kaffeine in apriProgrammi
- miglioramenti nella gestione do apertura e chiusura dei programmi
- inserito controllo volume
- risolto bug su radio che impediva l'esecuzione di varie condizioni (eliminato elif)
