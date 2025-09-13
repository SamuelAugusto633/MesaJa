# back/main_app.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Importa o nosso novo arquivo de rotas
import routes

# Cria a aplicação principal
app = FastAPI(
    title="MesaJa API",
    description="API para gerenciamento de fila de restaurante.",
    version="1.0.0"
)

# Monta um caminho para servir arquivos estáticos (CSS, Imagens) da pasta 'front'
app.mount("/static", StaticFiles(directory="../front"), name="static")

# Inclui todas as rotas definidas no arquivo routes.py
app.include_router(routes.router)