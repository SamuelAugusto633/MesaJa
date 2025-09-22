# back/routes.py
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import date

# Importa 
import crud
import schemas
import models
import reports
from database_config import get_db
from auth_logic import ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME, PASSWORD_HINT_1, PASSWORD_HINT_2
from notification_manager import get_notifications
from telegram_sender import enviar_mensagem_privada

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- Rotas de Autenticação e Páginas ---
@router.get("/", response_class=HTMLResponse, tags=["Páginas"])
async def read_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "message": None})

@router.post("/login", response_class=HTMLResponse, tags=["Autenticação"])
async def handle_login(request: Request, email: str = Form(...), password: str = Form(...)):
    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        error_message = "E-mail ou senha inválidos. Tente novamente."
        return templates.TemplateResponse("login.html", {"request": request, "message": error_message})

@router.get("/forgot-password", response_class=HTMLResponse, tags=["Autenticação"])
async def show_password_hints(request: Request):
    hints = f"{PASSWORD_HINT_1} {PASSWORD_HINT_2}"
    return templates.TemplateResponse("login.html", {"request": request, "message": hints})

@router.get("/dashboard", response_class=HTMLResponse, tags=["Páginas"])
async def show_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user_name": ADMIN_NAME})

@router.get("/status-mesas", response_class=HTMLResponse, tags=["Páginas"])
async def show_status_mesas_page(request: Request):
    return templates.TemplateResponse("status_mesas.html", {"request": request})

@router.get("/fila-atual", response_class=HTMLResponse, tags=["Páginas"])
async def show_fila_page(request: Request):
    return templates.TemplateResponse("fila.html", {"request": request})

@router.get("/central-interacoes", response_class=HTMLResponse, tags=["Páginas"])
async def show_interacoes_page(request: Request):
    return templates.TemplateResponse("central_interacoes.html", {"request": request})

@router.get("/menu-garcons", response_class=HTMLResponse, tags=["Páginas"])
async def show_garcons_page(request: Request):
    return templates.TemplateResponse("menu_garcons.html", {"request": request})

@router.get("/menu-promocional", response_class=HTMLResponse, tags=["Páginas"])
async def show_promocoes_page(request: Request):
    return templates.TemplateResponse("menu_promocional.html", {"request": request})

@router.get("/menu-relatorios", response_class=HTMLResponse, tags=["Páginas"])
async def show_relatorios_page(request: Request):
    return templates.TemplateResponse("menu_relatorios.html", {"request": request})

@router.get("/logout", tags=["Autenticação"])
async def handle_logout():
    return RedirectResponse(url="/", status_code=303)

# --- Rotas da API de Mesas ---
@router.post("/mesas/", response_model=schemas.MesaOut, tags=["Mesas"], status_code=201)
async def criar_nova_mesa(mesa: schemas.MesaCreate, db: Session = Depends(get_db)):
    try:
        nova_mesa = await crud.criar_mesa(db=db, mesa=mesa)
        return nova_mesa
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Uma mesa com este número já existe.")

@router.get("/mesas/", response_model=List[schemas.MesaOut], tags=["Mesas"])
def obter_mesas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.listar_mesas(db, skip=skip, limit=limit)

@router.put("/mesas/{mesa_id}", response_model=schemas.MesaOut, tags=["Mesas"])
async def mudar_status_mesa(mesa_id: int, mesa_update: schemas.MesaUpdate, db: Session = Depends(get_db)):
    mesa = await crud.atualizar_status_mesa(db, mesa_id=mesa_id, novo_status=mesa_update.status)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return mesa

@router.delete("/mesas/{mesa_id}", response_model=schemas.MesaOut, tags=["Mesas"])
async def remover_mesa(mesa_id: int, db: Session = Depends(get_db)):
    mesa_deletada = await crud.deletar_mesa(db, mesa_id=mesa_id)
    if not mesa_deletada:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return mesa_deletada

@router.post("/mesas/{mesa_id}/atribuir-proximo", response_model=schemas.MesaOut, tags=["Mesas"])
async def atribuir_cliente_mesa(mesa_id: int, db: Session = Depends(get_db)):
    mesa_atualizada = await crud.atribuir_proximo_cliente(db, mesa_id=mesa_id)
    if not mesa_atualizada:
        raise HTTPException(status_code=404, detail="Mesa não encontrada ou fila vazia.")
    return mesa_atualizada

# --- Rotas da API da Fila ---
#@router.post("/fila/", response_model=schemas.FilaOut, tags=["Fila"])
#async def entrar_na_fila(cliente: schemas.FilaCreate, db: Session = Depends(get_db)):
 #   return await crud.adicionar_cliente_fila(db=db, cliente=cliente)





@router.get("/mesas/{mesa_id}", response_model=schemas.MesaOut, tags=["Mesas"])
def obter_mesa_por_id(mesa_id: int, db: Session = Depends(get_db)):
    """Endpoint para buscar uma única mesa pelo seu ID."""
    mesa = crud.buscar_mesa_por_id(db, mesa_id=mesa_id)
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    return mesa



# retorna 201 auto indica que a criação foi bem-sucedida (“Created”).

#Sempre que alguém (bot do Telegram, aplicativo web ou outro cliente) quiser colocar um grupo 
# na fila de espera, ele envia os dados para esse endpoint, que grava no banco e retorna 
# a confirmação.
#

@router.post("/fila/", response_model=schemas.FilaOut, tags=["Fila"], status_code=201)
async def entrar_na_fila(cliente: schemas.FilaCreate, db: Session = Depends(get_db)):
    return await crud.adicionar_cliente_fila(db=db, cliente=cliente)



@router.get("/fila/", response_model=List[schemas.FilaOut], tags=["Fila"])
def obter_fila_espera(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.listar_fila(db, skip=skip, limit=limit)

@router.put("/fila/{fila_id}", response_model=schemas.FilaOut, tags=["Fila"])
async def modificar_cliente_fila(fila_id: int, cliente_update: schemas.FilaUpdate, db: Session = Depends(get_db)):
    cliente_atualizado = await crud.atualizar_cliente_fila(db, fila_id=fila_id, dados_atualizacao=cliente_update)
    if not cliente_atualizado:
        raise HTTPException(status_code=404, detail="Cliente na fila não encontrado")
    return cliente_atualizado

@router.post("/fila/atender-proximo", tags=["Fila"])
async def atender_proximo_cliente_da_fila(db: Session = Depends(get_db)):
    resultado = await crud.atender_proximo_da_fila(db)
    if not resultado["sucesso"]:
        raise HTTPException(status_code=409, detail=resultado["mensagem"])
    numeros_mesas = ", ".join([str(m.numero) for m in resultado["mesas"]])
    mensagem = f"Cliente {resultado['cliente'].nome_cliente} atendido na(s) Mesa(s) {numeros_mesas}."
    return {"detail": mensagem}
    
# --- Rotas da API da Central de Interações ---
@router.get("/historico-completo", response_model=List[schemas.FilaOut], tags=["Interações"])
def obter_historico_completo(db: Session = Depends(get_db)):
    return crud.listar_historico_completo(db)

@router.get("/metricas", tags=["Interações"])
def obter_metricas(db: Session = Depends(get_db)):
    return crud.calcular_metricas(db)

# --- Rotas da API de Garçons ---
@router.post("/garcons/", response_model=schemas.GarconOut, tags=["Garçons"])
async def criar_novo_garcon(garcon: schemas.GarconCreate, db: Session = Depends(get_db)):
    return await crud.criar_garcon(db=db, garcon=garcon)

@router.get("/garcons/", response_model=List[schemas.GarconOut], tags=["Garçons"])
def obter_garcons(db: Session = Depends(get_db)):
    return crud.listar_garcons(db)

@router.put("/garcons/{garcon_id}", response_model=schemas.GarconOut, tags=["Garçons"])
async def modificar_garcon(garcon_id: int, garcon_update: schemas.GarconUpdate, db: Session = Depends(get_db)):
    garcon_atualizado = await crud.atualizar_garcon(db, garcon_id=garcon_id, dados_atualizacao=garcon_update)
    if not garcon_atualizado:
        raise HTTPException(status_code=404, detail="Garçom não encontrado")
    return garcon_atualizado

@router.delete("/garcons/{garcon_id}", response_model=schemas.GarconOut, tags=["Garçons"])
async def remover_garcon(garcon_id: int, db: Session = Depends(get_db)):
    garcon_deletado = await crud.deletar_garcon(db, garcon_id=garcon_id)
    if not garcon_deletado:
        raise HTTPException(status_code=404, detail="Garçom não encontrado")
    return garcon_deletado



from telegram_sender import enviar_mensagem_privada, enviar_mensagem_para_grupo # Adicione o novo import

@router.post("/garcons/{garcon_id}/enviar-mensagem", response_model=schemas.MensagemOut, tags=["Garçons"])
async def enviar_mensagem_para_garcon(garcon_id: int, mensagem: schemas.MensagemEnvio, db: Session = Depends(get_db)):
    """
    Endpoint para o admin enviar uma mensagem para um garçom.
    Guarda a mensagem no banco, a envia via Telegram em privado E notifica o grupo.
    """
    garcon = crud.buscar_garcon_por_id(db, garcon_id=garcon_id)
    if not garcon:
        raise HTTPException(status_code=404, detail="Garçom não encontrado.")
    
    if not garcon.telegram_id:
        raise HTTPException(status_code=400, detail="Este garçom não tem um ID do Telegram cadastrado.")

    # 1. Envia a mensagem privada para o garçom
    sucesso_envio_privado = await enviar_mensagem_privada(user_id=garcon.telegram_id, mensagem=mensagem.texto)
    
    if not sucesso_envio_privado:
        raise HTTPException(status_code=500, detail="Falha ao enviar a mensagem privada para o Telegram.")

    # 2. Guarda a mensagem no nosso banco de dados
    mensagem_db = schemas.MensagemCreate(
        texto=mensagem.texto,
        direcao="enviada", # Mensagem enviada pelo admin
        garcon_id=garcon_id
    )
    mensagem_criada = await crud.criar_mensagem(db=db, mensagem=mensagem_db)

    # 3. (NOVO) Envia uma cópia da mensagem para o grupo
    mensagem_para_grupo = f"*(Admin para {garcon.nome})*: {mensagem.texto}"
    await enviar_mensagem_para_grupo(mensagem_para_grupo)
    
    return mensagem_criada


# rota conversas

@router.get("/garcons/by-telegram-id/{telegram_id}", response_model=schemas.GarconOut, tags=["Garçons"])
def obter_garcon_por_telegram_id(telegram_id: str, db: Session = Depends(get_db)):
    """Endpoint para encontrar um garçom pelo seu ID do Telegram."""
    garcon = crud.buscar_garcon_por_telegram_id(db, telegram_id=telegram_id)
    if not garcon:
        raise HTTPException(status_code=404, detail="Garçom com este ID do Telegram não foi encontrado.")
    return garcon



# --- Rotas da API de Promoções ---
@router.post("/promocoes/", response_model=schemas.PromocaoOut, tags=["Promoções"], status_code=201)
async def criar_nova_promocao(promocao: schemas.PromocaoCreate, db: Session = Depends(get_db)):
    return await crud.criar_promocao(db=db, promocao=promocao)

@router.get("/promocoes/", response_model=List[schemas.PromocaoOut], tags=["Promoções"])
def obter_promocoes(db: Session = Depends(get_db)):
    return crud.listar_promocoes(db)

@router.put("/promocoes/{promocao_id}", response_model=schemas.PromocaoOut, tags=["Promoções"])
async def modificar_promocao(promocao_id: int, promocao_update: schemas.PromocaoUpdate, db: Session = Depends(get_db)):
    promocao_atualizada = await crud.atualizar_promocao(db, promocao_id=promocao_id, dados_atualizacao=promocao_update)
    if not promocao_atualizada:
        raise HTTPException(status_code=404, detail="Promoção não encontrada")
    return promocao_atualizada

@router.delete("/promocoes/{promocao_id}", response_model=schemas.PromocaoOut, tags=["Promoções"])
async def remover_promocao(promocao_id: int, db: Session = Depends(get_db)):
    promocao_deletada = await crud.deletar_promocao(db, promocao_id=promocao_id)
    if not promocao_deletada:
        raise HTTPException(status_code=404, detail="Promoção não encontrada")
    return promocao_deletada

# --- Rotas da API de Mensagens ---
@router.post("/mensagens/", response_model=schemas.MensagemOut, tags=["Mensagens"])
async def enviar_nova_mensagem(mensagem: schemas.MensagemCreate, db: Session = Depends(get_db)):
    garcon = crud.buscar_garcon_por_id(db, garcon_id=mensagem.garcon_id)
    if not garcon:
        raise HTTPException(status_code=404, detail="Garçom não encontrado para associar a mensagem.")
    return await crud.criar_mensagem(db=db, mensagem=mensagem)

@router.get("/mensagens/{garcon_id}", response_model=List[schemas.MensagemOut], tags=["Mensagens"])
def obter_conversa_garcon(garcon_id: int, db: Session = Depends(get_db)):
    return crud.listar_mensagens_por_garcon(db, garcon_id=garcon_id)

# --- Rotas da API de Notificações ---
@router.get("/notificacoes/", response_model=List[str], tags=["Notificações"])
def ler_notificacoes():
    return get_notifications()
    
# --- Rotas da API de Relatórios ---
@router.get("/relatorios/diario", tags=["Relatórios"])
def gerar_relatorio_diario(db: Session = Depends(get_db)):
    try:
        caminho_pdf = reports.gerar_relatorio_diario_pdf(db)
        return FileResponse(path=caminho_pdf, media_type='application/pdf', filename=caminho_pdf.split('/')[-1])
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao gerar o relatório PDF.")

@router.get("/relatorios/semanal", tags=["Relatórios"])
def gerar_relatorio_semanal(db: Session = Depends(get_db)):
    try:
        caminho_pdf = reports.gerar_relatorio_semanal_pdf(db)
        return FileResponse(path=caminho_pdf, media_type='application/pdf', filename=caminho_pdf.split('/')[-1])
    except Exception as e:
        print(f"Erro ao gerar relatório semanal: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao gerar o relatório PDF.")

@router.get("/relatorios/personalizado", tags=["Relatórios"])
def gerar_relatorio_personalizado(data_inicio: date, data_fim: date, db: Session = Depends(get_db)):
    try:
        caminho_pdf = reports.gerar_relatorio_personalizado_pdf(db, data_inicio=data_inicio, data_fim=data_fim)
        return FileResponse(path=caminho_pdf, media_type='application/pdf', filename=caminho_pdf.split('/')[-1])
    except Exception as e:
        print(f"Erro ao gerar relatório personalizado: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao gerar o relatório PDF.")