🍽️ MesaJa - Sistema de Gerenciamento de Restaurante


Sistema de gerenciamento de mesas para restaurantes, composto por um Painel Web para administradores e um Bot do Telegram para interação com a equipa.

🏗️ Estrutura do Projeto


Este repositório contém todo o código do back-end (API, lógica do servidor, interação com o banco de dados e testes).

O código do front-end (a interface visual construída para interagir com esta API) encontra-se num repositório separado. Para obter a aplicação completa, é necessário ter os dois projetos.

Clone o repositório do front-end com o seguinte comando:

git clone [https://github.com/SamuelAugusto633/MesaJa_Front.git](https://github.com/SamuelAugusto633/MesaJa_Front.git)

Certifique-se de que a pasta front do repositório está presente na raiz do projeto MesaJa, fora da pasta back.

🚀 Tutorial Completo de Instalação e Execução

Siga os passos abaixo para configurar e rodar o projeto localmente.
1. Pré-requisitos

    Python 3.10+

    PostgreSQL

    Git

2. Instalação

a. Clone o repositório:

git clone [https://github.com/SEU_USUARIO/MesaJa.git](https://github.com/SEU_USUARIO/MesaJa.git)
cd MesaJa

b. Crie e ative o ambiente virtual:

# Crie o ambiente na pasta raiz 'MesaJa'
python -m venv venv

# Ative o ambiente
# No Linux / macOS:
source venv/bin/activate
# No Windows:
# venv\Scripts\activate

c. Instale as dependências:
(Certifique-se de que o seu ficheiro requirements.txt está na pasta back)

pip install -r back/requirements.txt

d. Crie as Tabelas no Banco de Dados:

# A partir da pasta raiz 'MesaJa/', com o ambiente virtual ativo
cd back
python init_db.py

3. Execução do Sistema

Para o sistema funcionar completamente, é preciso executar dois processos em dois terminais diferentes.

Terminal 1: Servidor Web (Painel do Administrador)

# A partir da pasta raiz 'MesaJa/', com o ambiente virtual ativo
cd back
uvicorn main_app:app --reload

    A aplicação estará disponível em http://127.0.0.1:8000

Terminal 2: Bot "Ouvinte" do Telegram

# A partir da pasta raiz 'MesaJa/', com o ambiente virtual ativo
cd back
python bot_listener.py

    Este terminal ficará a "ouvir" as mensagens enviadas pelos garçons.

4. Execução dos Testes Locais

Para verificar a integridade do back-end, execute os testes automatizados com pytest.

# A partir da pasta raiz 'MesaJa/', com o ambiente virtual ativo
pytest -v -s

