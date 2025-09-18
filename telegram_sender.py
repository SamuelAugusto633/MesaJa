

import os
import telegram
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_GROUP_CHAT_ID = os.getenv("TELEGRAM_GROUP_CHAT_ID")

async def enviar_mensagem_para_grupo(mensagem: str):
    """
    Envia uma mensagem de texto para o grupo de garçons no Telegram.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_GROUP_CHAT_ID:
        print("AVISO: Token do Telegram ou ID do Chat não configurado. Mensagem não enviada.")
        return

    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        mensagem_escapada = mensagem.replace('.', '\\.').replace('-', '\\-').replace('!', '\\!').replace('(', '\\(').replace(')', '\\)')
        
        await bot.send_message(
            chat_id=TELEGRAM_GROUP_CHAT_ID, 
            text=mensagem_escapada, 
            parse_mode='MarkdownV2'
        )
        print(f"Mensagem enviada para o grupo do Telegram.")
    except Exception as e:
        print(f"ERRO ao enviar mensagem para o Telegram: {e}")


async def enviar_mensagem_privada(user_id: str, mensagem: str):
    """
    Envia uma mensagem de texto privada para um utilizador específico do Telegram.
    """
    if not TELEGRAM_BOT_TOKEN:
        print("AVISO: Token do Telegram não configurado. Mensagem não enviada.")
        return False
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        mensagem_escapada = mensagem.replace('.', '\\.').replace('-', '\\-').replace('!', '\\!')
        
        await bot.send_message(chat_id=user_id, text=mensagem_escapada, parse_mode='MarkdownV2')
        print(f"Mensagem enviada para o utilizador {user_id}.")
        return True
    except Exception as e:
        print(f"ERRO ao enviar mensagem privada para {user_id}: {e}")
        return False