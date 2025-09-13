# back/schemas.py

from pydantic import BaseModel, ConfigDict
from typing import Optional

# Em back/schemas.py

class MesaBase(BaseModel):
    numero: int
    capacidade: int
    status: Optional[str] = "disponivel"
    cliente_atual: Optional[str] = None # <-- ADICIONE ESTA LINHA

# Schema para criar uma nova mesa (o que a API recebe)
class MesaCreate(MesaBase):
    pass

# Schema para ler os dados de uma mesa (o que a API envia de volta)
class MesaOut(MesaBase):
    id: int

    # Configuração para permitir que o Pydantic leia dados de um objeto SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

# Schema para atualização (o que a API recebe para um PUT/PATCH)
class MesaUpdate(BaseModel):
    status: Optional[str] = None
    

from datetime import datetime

# --- Schemas para a Fila ---

class FilaBase(BaseModel):
    nome_cliente: str
    tamanho_grupo: int

class FilaCreate(FilaBase):
    pass

class FilaOut(FilaBase):
    id: int
    status: str
    horario_chegada: datetime

    model_config = ConfigDict(from_attributes=True)
    
    


class FilaUpdate(BaseModel):
    nome_cliente: Optional[str] = None
    tamanho_grupo: Optional[int] = None
    status: Optional[str] = None
    
    
    


# --- Schemas para Garçons ---

class GarconBase(BaseModel):
    nome: str
    telegram_id: Optional[str] = None
    status: Optional[str] = "ativo"

class GarconCreate(GarconBase):
    pass

class GarconUpdate(BaseModel):
    nome: Optional[str] = None
    telegram_id: Optional[str] = None
    status: Optional[str] = None

class GarconOut(GarconBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
    
    
    


# --- Schemas para Promoções ---

class PromocaoBase(BaseModel):
    nome: str
    descricao: str
    regras: Optional[str] = None
    status: Optional[str] = "ativa"

class PromocaoCreate(PromocaoBase):
    pass

class PromocaoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    regras: Optional[str] = None
    status: Optional[str] = None

class PromocaoOut(PromocaoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
    
    
    

# --- Schemas para Mensagens ---

class MensagemBase(BaseModel):
    texto: str
    direcao: str # "enviada" (admin -> garçom) ou "recebida" (garçom -> admin)
    garcon_id: int

class MensagemCreate(MensagemBase):
    pass

class MensagemOut(MensagemBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
    
    
    


class MensagemEnvio(BaseModel):
    texto: str