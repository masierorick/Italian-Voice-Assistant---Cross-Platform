import socket

# ==================================
# CONTROLLO MODALITA' ONLINE/OFFLINE
# ==================================
def check_connectivity(timeout=1.5):
    """Controllo connessione internet una sola volta."""
    try:
        with socket.create_connection(
            ("142.250.184.4", 443),
            timeout=timeout
        ):
            return True
    except OSError:
        return False


ONLINE_MODE = check_connectivity()
