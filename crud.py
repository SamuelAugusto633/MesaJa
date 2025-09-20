# back/crud.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from itertools import combinations
from datetime import date, datetime, timedelta

import models
import schemas
from notification_manager import add_notification
from telegram_sender import enviar_mensagem_para_grupo, enviar_mensagem_privada

# --- Funções CRUD para a Mesa ---

async def criar_mesa(db: Session, mesa: schemas.MesaCreate):
    """Cria uma nova entrada de mesa no banco de dados."""
    nova_mesa = models.Mesa(**mesa.model_dump())
    db.add(nova_mesa)
    db.commit()
    db.refresh(nova_mesa)
    add_notification(f"Mesa {nova_mesa.numero} foi criada com capacidade para {nova_mesa.capacidade}.")
    return nova_mesa

def listar_mesas(db: Session, skip: int = 0, limit: int = 100):
    """Lista todas as mesas do banco de dados."""
    return db.query(models.Mesa).offset(skip).limit(limit).all()

def buscar_mesa_por_id(db: Session, mesa_id: int):
    """Busca uma única mesa pelo seu ID."""
    return db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()

async def atualizar_status_mesa(db: Session, mesa_id: int, novo_status: str):
    """Atualiza o status de uma mesa específica no banco de dados."""
    mesa = buscar_mesa_por_id(db, mesa_id)
    if mesa:
        cliente_info = f" por '{mesa.cliente_atual}'" if mesa.cliente_atual else ""
        add_notification(f"Mesa {mesa.numero}{cliente_info} teve seu status alterado para '{novo_status}'.")
        
        mesa.status = novo_status
        if novo_status in ["disponivel", "suja"]:
            mesa.cliente_atual = None
            
        db.commit()
        db.refresh(mesa)
    return mesa

async def deletar_mesa(db: Session, mesa_id: int):
    """Deleta uma mesa do banco de dados pelo seu ID."""
    mesa = buscar_mesa_por_id(db, mesa_id)
    if mesa:
        add_notification(f"Mesa {mesa.numero} foi deletada do sistema.")
        db.delete(mesa)
        db.commit()
    return mesa

async def atribuir_proximo_cliente(db: Session, mesa_id: int):
    """Atribui o primeiro cliente da fila a uma mesa disponível."""
    mesa = buscar_mesa_por_id(db, mesa_id)
    cliente_fila = db.query(models.Fila).filter(models.Fila.status == 'aguardando').order_by(models.Fila.horario_chegada).first()

    if mesa and cliente_fila:
        mesa.status = "ocupada"
        mesa.cliente_atual = cliente_fila.nome_cliente
        
        cliente_fila.status = "atendido"
        cliente_fila.horario_atendimento = datetime.utcnow()
        cliente_fila.mesas_utilizadas = str(mesa.numero)
        
        db.commit()
        db.refresh(mesa)
        add_notification(f"Cliente '{cliente_fila.nome_cliente}' foi alocado à Mesa {mesa.numero}.")
        mensagem_para_grupo = f"Cliente '{cliente_fila.nome_cliente}' foi atendido na Mesa {mesa.numero}."
        await enviar_mensagem_para_grupo(mensagem_para_grupo)
        
        return mesa
    
    return None

# --- Funções CRUD para a Fila ---

async def adicionar_cliente_fila(db: Session, cliente: schemas.FilaCreate):
    """Adiciona um novo cliente na fila de espera."""
    novo_cliente = models.Fila(**cliente.model_dump())
    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)
    add_notification(f"Cliente '{novo_cliente.nome_cliente}' (grupo de {novo_cliente.tamanho_grupo}) entrou na fila.")
    return novo_cliente

def listar_fila(db: Session, skip: int = 0, limit: int = 100):
    """Lista os clientes na fila com o status 'aguardando'."""
    return db.query(models.Fila).filter(models.Fila.status == 'aguardando').order_by(models.Fila.horario_chegada).offset(skip).limit(limit).all()

def buscar_cliente_fila_por_id(db: Session, fila_id: int):
    """Busca um cliente na fila pelo seu ID."""
    return db.query(models.Fila).filter(models.Fila.id == fila_id).first()

async def atualizar_cliente_fila(db: Session, fila_id: int, dados_atualizacao: schemas.FilaUpdate):
    """Atualiza os dados de um cliente na fila."""
    cliente_db = buscar_cliente_fila_por_id(db, fila_id)
    if cliente_db:
        dados = dados_atualizacao.model_dump(exclude_unset=True)
        for campo, valor in dados.items():
            setattr(cliente_db, campo, valor)
        
        if dados.get('status') == 'atendido':
            cliente_db.horario_atendimento = datetime.utcnow()

        if 'status' in dados:
            add_notification(f"Status do cliente '{cliente_db.nome_cliente}' alterado para '{dados['status']}'.")
            
        db.commit()
        db.refresh(cliente_db)
    return cliente_db

async def atender_proximo_da_fila(db: Session):
    """Busca o primeiro cliente na fila e tenta alocá-lo a uma ou mais mesas."""
    cliente_fila = db.query(models.Fila).filter(models.Fila.status == 'aguardando').order_by(models.Fila.horario_chegada).first()
    if not cliente_fila:
        return {"sucesso": False, "mensagem": "A fila de espera está vazia."}

    mesas_disponiveis = db.query(models.Mesa).filter(models.Mesa.status == 'disponivel').order_by(models.Mesa.capacidade.desc()).all()
    
    mesas_alocadas = None
    # 1. Tenta encontrar uma única mesa
    for mesa_unica in mesas_disponiveis:
        if mesa_unica.capacidade >= cliente_fila.tamanho_grupo:
            mesas_alocadas = [mesa_unica]
            break
            
    # 2. Se não encontrou, tenta combinar
    if not mesas_alocadas and cliente_fila.tamanho_grupo > 4 and len(mesas_disponiveis) >= 2:
        for combo in combinations(mesas_disponiveis, 2):
            if sum(m.capacidade for m in combo) >= cliente_fila.tamanho_grupo:
                mesas_alocadas = list(combo)
                break

    if mesas_alocadas:
        numeros_mesas_str = ", ".join(str(m.numero) for m in mesas_alocadas)
        for mesa in mesas_alocadas:
            mesa.status = "ocupada"
            mesa.cliente_atual = cliente_fila.nome_cliente
        
        cliente_fila.status = "atendido"
        cliente_fila.horario_atendimento = datetime.utcnow()
        cliente_fila.mesas_utilizadas = numeros_mesas_str
        
        db.commit()
        
        add_notification(f"Cliente '{cliente_fila.nome_cliente}' atendido na(s) Mesa(s) {numeros_mesas_str}.")
        mensagem_para_grupo = f"Cliente '{cliente_fila.nome_cliente}' foi atendido na(s) Mesa(s) {numeros_mesas_str}."
        await enviar_mensagem_para_grupo(mensagem_para_grupo)

        return {"sucesso": True, "cliente": cliente_fila, "mesas": mesas_alocadas}

    return {"sucesso": False, "mensagem": "Não há mesas ou combinação de mesas disponíveis que comportem o grupo."}

# --- Funções para a Central de Interações e Relatórios ---

def listar_historico_completo(db: Session, limit: int = 50):
    return db.query(models.Fila).order_by(models.Fila.horario_chegada.desc()).limit(limit).all()

def calcular_metricas(db: Session):
    """Calcula as métricas para o dashboard de interações."""
    hoje = date.today()
    clientes_na_fila = db.query(func.count(models.Fila.id)).filter(models.Fila.status == 'aguardando').scalar() or 0
    desistencias_hoje = db.query(func.count(models.Fila.id)).filter(
        models.Fila.status == 'cancelado',
        func.date(models.Fila.horario_chegada) == hoje
    ).scalar() or 0
    
    numero_promocoes = contar_total_promocoes(db)

    return {
        "clientes_na_fila": clientes_na_fila,
        "desistencias_hoje": desistencias_hoje,
        "numero_promocoes": numero_promocoes
    }

def contar_clientes_por_status_no_dia(db: Session, status: str, dia: date):
    return db.query(func.count(models.Fila.id)).filter(
        models.Fila.status == status,
        func.date(models.Fila.horario_chegada) == dia
    ).scalar() or 0

def contar_total_mesas(db: Session):
    return db.query(func.count(models.Mesa.id)).scalar() or 0

def listar_clientes_do_dia(db: Session, dia: date):
    return db.query(models.Fila).filter(
        func.date(models.Fila.horario_chegada) == dia
    ).order_by(models.Fila.horario_chegada).all()

def listar_clientes_atendidos_no_dia(db: Session, dia: date):
    return db.query(models.Fila).filter(
        models.Fila.status == 'atendido',
        func.date(models.Fila.horario_chegada) == dia,
        models.Fila.horario_atendimento != None
    ).all()
    
def contar_total_promocoes(db: Session):
    """Conta o total de promoções cadastradas."""
    return db.query(func.count(models.Promocao.id)).scalar() or 0

def listar_clientes_da_semana(db: Session, hoje: date):
    """Busca a lista de todos os clientes que entraram na fila nos últimos 7 dias."""
    data_inicio = hoje - timedelta(days=6)
    return db.query(models.Fila).filter(
        func.date(models.Fila.horario_chegada) >= data_inicio,
        func.date(models.Fila.horario_chegada) <= hoje
    ).order_by(models.Fila.horario_chegada).all()

def listar_clientes_por_periodo(db: Session, data_inicio: date, data_fim: date):
    """Busca a lista de todos os clientes que entraram na fila num período específico."""
    return db.query(models.Fila).filter(
        func.date(models.Fila.horario_chegada) >= data_inicio,
        func.date(models.Fila.horario_chegada) <= data_fim
    ).order_by(models.Fila.horario_chegada).all()

# --- Funções CRUD para Garçons ---

async def criar_garcon(db: Session, garcon: schemas.GarconCreate):
    """Cria um novo garçom no banco de dados."""
    novo_garcon = models.Garcon(**garcon.model_dump())
    db.add(novo_garcon)
    db.commit()
    db.refresh(novo_garcon)
    add_notification(f"Garçom '{novo_garcon.nome}' foi adicionado ao sistema.")
    return novo_garcon

def listar_garcons(db: Session):
    """Lista todos os garçons do banco de dados."""
    return db.query(models.Garcon).order_by(models.Garcon.nome).all()

def buscar_garcon_por_id(db: Session, garcon_id: int):
    """Busca um garçom pelo seu ID."""
    return db.query(models.Garcon).filter(models.Garcon.id == garcon_id).first()

async def atualizar_garcon(db: Session, garcon_id: int, dados_atualizacao: schemas.GarconUpdate):
    """Atualiza os dados de um garçom."""
    garcon_db = buscar_garcon_por_id(db, garcon_id)
    if garcon_db:
        dados = dados_atualizacao.model_dump(exclude_unset=True)
        for campo, valor in dados.items():
            setattr(garcon_db, campo, valor)
        db.commit()
        db.refresh(garcon_db)
        add_notification(f"Dados do garçom '{garcon_db.nome}' foram atualizados.")
    return garcon_db

async def deletar_garcon(db: Session, garcon_id: int):
    """Deleta um garçom do sistema."""
    garcon_db = buscar_garcon_por_id(db, garcon_id)
    if garcon_db:
        nome_garcon = garcon_db.nome
        db.delete(garcon_db)
        db.commit()
        add_notification(f"Garçom '{nome_garcon}' foi removido do sistema.")
    return garcon_db



# ouvinte

def buscar_garcon_por_telegram_id(db: Session, telegram_id: str):
    """Busca um garçom pelo seu ID do Telegram."""
    return db.query(models.Garcon).filter(models.Garcon.telegram_id == telegram_id).first()





# --- Funções CRUD para Promoções ---

async def criar_promocao(db: Session, promocao: schemas.PromocaoCreate):
    """Cria uma nova promoção no banco de dados e notifica o grupo do Telegram."""
    nova_promocao = models.Promocao(**promocao.model_dump())
    db.add(nova_promocao)
    db.commit()
    db.refresh(nova_promocao)
    add_notification(f"Promoção '{nova_promocao.nome}' foi criada.")
    
    mensagem_telegram = (
        f"*Nova Promoção Ativa!*\n\n"
        f"*{nova_promocao.nome}*\n"
        f"{nova_promocao.descricao}\n\n"
        f"_Regras: {nova_promocao.regras or 'N/A'}_"
    )
    await enviar_mensagem_para_grupo(mensagem_telegram)
    
    return nova_promocao

def listar_promocoes(db: Session):
    """Lista todas as promoções do banco de dados."""
    return db.query(models.Promocao).order_by(models.Promocao.nome).all()

def buscar_promocao_por_id(db: Session, promocao_id: int):
    """Busca uma promoção pelo seu ID."""
    return db.query(models.Promocao).filter(models.Promocao.id == promocao_id).first()

async def atualizar_promocao(db: Session, promocao_id: int, dados_atualizacao: schemas.PromocaoUpdate):
    """Atualiza os dados de uma promoção."""
    promocao_db = buscar_promocao_por_id(db, promocao_id)
    if promocao_db:
        dados = dados_atualizacao.model_dump(exclude_unset=True)
        for campo, valor in dados.items():
            setattr(promocao_db, campo, valor)
        db.commit()
        db.refresh(promocao_db)
        add_notification(f"Promoção '{promocao_db.nome}' foi atualizada.")
    return promocao_db

async def deletar_promocao(db: Session, promocao_id: int):
    """Deleta uma promoção do sistema."""
    promocao_db = buscar_promocao_por_id(db, promocao_id)
    if promocao_db:
        nome_promocao = promocao_db.nome
        db.delete(promocao_db)
        db.commit()
        add_notification(f"Promoção '{nome_promocao}' foi removida.")
    return promocao_db

# --- Funções CRUD para Mensagens ---

async def criar_mensagem(db: Session, mensagem: schemas.MensagemCreate):
    """Cria uma nova mensagem no banco de dados."""
    nova_mensagem = models.Mensagem(**mensagem.model_dump())
    db.add(nova_mensagem)
    db.commit()
    db.refresh(nova_mensagem)
    return nova_mensagem

def listar_mensagens_por_garcon(db: Session, garcon_id: int):
    """Lista todas as mensagens de uma conversa com um garçom específico."""
    return db.query(models.Mensagem).filter(models.Mensagem.garcon_id == garcon_id).order_by(models.Mensagem.timestamp).all()