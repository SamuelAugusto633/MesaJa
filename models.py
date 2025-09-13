# back/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database_config import Base
from datetime import datetime

class Mesa(Base):
    __tablename__ = "mesas"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, nullable=False)
    capacidade = Column(Integer, nullable=False)
    status = Column(String, default="disponivel")
    cliente_atual = Column(String, nullable=True)

class Fila(Base):
    __tablename__ = "fila"
    id = Column(Integer, primary_key=True, index=True)
    nome_cliente = Column(String, nullable=False)
    tamanho_grupo = Column(Integer, nullable=False)
    status = Column(String, default="aguardando")
    horario_chegada = Column(DateTime, default=datetime.utcnow)
    horario_atendimento = Column(DateTime, nullable=True)
    

class Garcon(Base):
    __tablename__ = "garcons"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    telegram_id = Column(String, unique=True, nullable=True)
    status = Column(String, default="ativo")
    mensagens = relationship("Mensagem", back_populates="garcon")

class Promocao(Base):
    __tablename__ = "promocoes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    descricao = Column(String, nullable=False)
    regras = Column(String, nullable=True)
    status = Column(String, default="ativa")

class Mensagem(Base):
    __tablename__ = "mensagens"
    id = Column(Integer, primary_key=True, index=True)
    texto = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    direcao = Column(String, nullable=False) 
    garcon_id = Column(Integer, ForeignKey("garcons.id"))
    garcon = relationship("Garcon", back_populates="mensagens")