# back/auth_logic.py

# --- DADOS HARDCODED ---
# Em uma aplicação real, isso viria de um banco de dados.
# Para o nosso projeto, os dados do administrador são definidos aqui.

ADMIN_EMAIL = "admin@mesaja.com"
ADMIN_PASSWORD = "123"
ADMIN_NAME = "Administrador" # Nome que aparecerá na tela após o login

# Dicas para a senha
PASSWORD_HINT_1 = "Dica 1: A senha tem 3 dígitos."
PASSWORD_HINT_2 = "Dica 2: É uma sequência numérica simples."