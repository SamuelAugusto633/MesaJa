# back/bot_listener.py

import nest_asyncio
nest_asyncio.apply()

import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# Carrega as variáveis de ambiente
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = "http://127.0.0.1:8000"

# --- Lógica da Conversa para Clientes ---
NOME, TAMANHO_GRUPO = range(2)

async def start_fila(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Olá! Bem-vindo ao MesaJa. Para entrar na fila, por favor, diga-me o seu nome e sobrenome."
    )
    return NOME

async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['nome_cliente'] = update.message.text
    await update.message.reply_text(
        f"Ótimo, {update.message.text}. E para quantas pessoas é a mesa?"
    )
    return TAMANHO_GRUPO

async def receber_tamanho_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nome_cliente = context.user_data['nome_cliente']
    # Guardamos o ID do Telegram do cliente para futuras notificações
    cliente_telegram_id = str(update.message.from_user.id)
    
    try:
        tamanho_grupo = int(update.message.text)
        if tamanho_grupo <= 0: raise ValueError()

        # --- NOVA VALIDAÇÃO DE TAMANHO ---
        if tamanho_grupo > 8:
            await update.message.reply_text(
                "Para grupos com mais de 8 pessoas, por favor, contacte diretamente o restaurante para fazer uma reserva especial. Obrigado!"
            )
            context.user_data.clear()
            return ConversationHandler.END

        print(f"Adicionando à fila via bot: {nome_cliente}, {tamanho_grupo} pessoas")

        # Enviamos também o ID do telegram para o back-end
        fila_data = {
            "nome_cliente": nome_cliente, 
            "tamanho_grupo": tamanho_grupo,
            "cliente_telegram_id": cliente_telegram_id 
        }
        response = requests.post(f"{API_BASE_URL}/fila/", json=fila_data)

        if response.status_code == 201:
            await update.message.reply_text("Perfeito! Adicionei o seu grupo à fila de espera. Iremos notificá-lo em breve quando a sua mesa estiver pronta.")
            print("Cliente adicionado à fila com sucesso via bot.")
        else:
            await update.message.reply_text("Desculpe, não foi possível adicioná-lo à fila. O sistema parece estar com problemas.")
            print(f"Erro ao adicionar cliente via API: {response.text}")

    except ValueError:
        await update.message.reply_text("Isso não parece ser um número válido. Por favor, envie apenas o número de pessoas.")
        return TAMANHO_GRUPO
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Pedido para entrar na fila cancelado.")
    context.user_data.clear()
    return ConversationHandler.END





# --- Lógica para Mensagens de Garçons ---
async def handle_garcon_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lida com mensagens normais que podem ser de garçons."""
    user_id = str(update.message.from_user.id)
    texto_mensagem = update.message.text
    
    try:
        response = requests.get(f"{API_BASE_URL}/garcons/by-telegram-id/{user_id}")
        if response.status_code == 200:
            garcon = response.json()
            mensagem_data = {"texto": texto_mensagem, "direcao": "recebida", "garcon_id": garcon['id']}
            requests.post(f"{API_BASE_URL}/mensagens/", json=mensagem_data)
            await update.message.reply_text("Mensagem recebida pelo sistema.")
        else:
            # Se não for um garçom, assume que não é para o sistema
            await update.message.reply_text("Olá! Se quiser entrar na fila, por favor, use o comando /entrar.")
    except requests.exceptions.RequestException as e:
        print(f"ERRO de API ao lidar com mensagem de garçom: {e}")

# --- Função Principal do Bot ---
def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        print("ERRO: TELEGRAM_BOT_TOKEN não encontrado no ficheiro .env")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Cria o ConversationHandler para o fluxo de entrada na fila
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("entrar", start_fila)],
        states={
            NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)],
            TAMANHO_GRUPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_tamanho_grupo)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )

    application.add_handler(conv_handler)
    
    # Adiciona o handler para mensagens normais (deve vir depois da conversa)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_garcon_message))

    print("Bot 'ouvinte' iniciado. A aguardar mensagens e comandos...")
    application.run_polling()

if __name__ == "__main__":
    main()