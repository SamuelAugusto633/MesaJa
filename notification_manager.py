

from collections import deque
from datetime import datetime

# Usamos um 'deque' com um tamanho máximo. Ele automaticamente remove
# o item mais antigo quando um novo é adicionado e a lista está cheia.
notifications = deque(maxlen=5)

def add_notification(message: str):
    """Adiciona uma nova notificação à lista."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    notifications.appendleft(f"[{timestamp}] {message}")

def get_notifications():
    """Retorna a lista de notificações atuais."""
    return list(notifications)

# Adiciona uma notificação inicial
add_notification("Sistema iniciado. Bem-vindo!")