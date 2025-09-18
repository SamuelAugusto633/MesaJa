# back/init_db.py

from database_config import Base, engine
from models import Mesa, Fila, Garcon, Promocao, Mensagem 

def create_tables():
    """
    Cria todas as tabelas no banco de dados que foram definidas usando a Base.
    """
    print("A verificar/criar tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas verificadas/criadas com sucesso!")

if __name__ == "__main__":
    create_tables()