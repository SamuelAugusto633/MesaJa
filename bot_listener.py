# back/bot_listener.py

import nest_asyncio
nest_asyncio.apply()

import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Carrega as variáveis de ambiente
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = "http://127.0.0.1:8000" # A morada da nossa API MesaJa

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Esta função é chamada sempre que o bot recebe uma mensagem.
    """
    if not update.message or not update.message.text:
        return

    user_id = str(update.message.from_user.id)
    texto_mensagem = update.message.text
    nome_utilizador = update.message.from_user.first_name

    print(f"Mensagem recebida de {nome_utilizador} (ID: {user_id}): '{texto_mensagem}'")

    # 1. Verificar se o remetente é um garçom registado
    try:
        response = requests.get(f"{API_BASE_URL}/garcons/by-telegram-id/{user_id}")
        
        if response.status_code == 200:
            garcon = response.json()
            garcon_id_db = garcon['id']
            print(f"Remetente identificado como o garçom: {garcon['nome']}")

            # 2. Se for um garçom, guardar a mensagem na nossa base de dados
            mensagem_data = {
                "texto": texto_mensagem,
                "direcao": "recebida", # Mensagem recebida de um garçom
                "garcon_id": garcon_id_db
            }
            post_response = requests.post(f"{API_BASE_URL}/mensagens/", json=mensagem_data)
            
            if post_response.status_code == 200:
                print("Mensagem guardada com sucesso na base de dados do MesaJa.")
                await update.message.reply_text("Mensagem recebida pelo sistema.")
            else:
                print(f"Erro ao guardar mensagem na API: {post_response.text}")
                await update.message.reply_text("Ocorreu um erro ao processar a sua mensagem.")
        else:
            print("Remetente não é um garçom registado. A ignorar.")
            await update.message.reply_text(f"Olá {nome_utilizador}! Este é um canal de comunicação interno do MesaJa. Não estou autorizado a falar consigo.")

    except requests.exceptions.RequestException as e:
        print(f"ERRO: Não foi possível comunicar com a API do MesaJa. Verifique se o servidor está a correr. Detalhes: {e}")
        await update.message.reply_text("Não foi possível comunicar com o sistema MesaJa neste momento.")


def main() -> None:
    """Inicia o bot."""
    if not TELEGRAM_BOT_TOKEN:
        print("ERRO: TELEGRAM_BOT_TOKEN não encontrado no ficheiro .env")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot 'ouvinte' iniciado. A aguardar mensagens...")
    
    application.run_polling()

if __name__ == "__main__":
    main()