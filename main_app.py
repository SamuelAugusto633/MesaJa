# back/main_app.py

#from fastapi import FastAPI
#from fastapi.staticfiles import StaticFiles


#import routes

# Cria a aplicação principal
#app = FastAPI(
#    title="MesaJa API",
 #   description="API para gerenciamento de fila de restaurante.",
#    version="1.0.0"
#)

# Monta um caminho para servir arquivos estáticos (CSS, Imagens) da pasta 'front'
#app.mount("/static", StaticFiles(directory="../front"), name="static")

# Inclui todas as rotas definidas no arquivo routes.py
#app.include_router(routes.router)





from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os


import routes


# Descobre o caminho absoluto para a pasta 'back' 
# e depois para a pasta 'front'
current_dir = os.path.dirname(os.path.abspath(__file__))
front_dir = os.path.join(current_dir, "..", "front")







# Cria a aplicação principal
app = FastAPI(
    title="MesaJa API",
    description="API para gerenciamento de fila de restaurante.",
    version="1.0.0"
)

# Monta um caminho para servir arquivos estáticos usando o caminho absoluto

if os.path.isdir(front_dir):
    app.mount("/static", StaticFiles(directory=front_dir), name="static")

# Inclui todas as rotas definidas no arquivo routes.py
app.include_router(routes.router)