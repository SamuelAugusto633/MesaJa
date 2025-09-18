# back/tests/test_mesas.py
from fastapi.testclient import TestClient



def test_criar_mesa(client: TestClient):
    """Testa se conseguimos criar uma nova mesa."""
    response = client.post("/mesas/", json={"numero": 101, "capacidade": 4})
    assert response.status_code == 201
    data = response.json()
    assert data["numero"] == 101
    assert data["capacidade"] == 4

def test_listar_mesas(client: TestClient):
    """Testa a listagem de mesas."""
    # Cria uma mesa primeiro para garantir que a lista não está vazia
    client.post("/mesas/", json={"numero": 102, "capacidade": 2})
    
    response = client.get("/mesas/")
    assert response.status_code == 200
    lista = response.json()
    assert isinstance(lista, list)
    assert len(lista) >= 1
 
    assert any(m["numero"] == 102 for m in lista)

def test_impedir_mesa_duplicada(client: TestClient):
    """Testa se a API impede a criação de uma mesa com um número duplicado."""
    client.post("/mesas/", json={"numero": 103, "capacidade": 2})
    response = client.post("/mesas/", json={"numero": 103, "capacidade": 2})
    assert response.status_code == 409


def test_atualizar_status_mesa(client: TestClient):
    """Testa se conseguimos atualizar o status de uma mesa."""
    # 1. Cria uma nova mesa
    response_criacao = client.post("/mesas/", json={"numero": 104, "capacidade": 6})
    assert response_criacao.status_code == 201
    mesa_id = response_criacao.json()["id"]

    # 2. Atualiza o status para "suja"
    response_update = client.put(f"/mesas/{mesa_id}", json={"status": "suja"})
    
    # 3. Verifica se a atualização foi bem-sucedida
    assert response_update.status_code == 200
    data = response_update.json()
    assert data["status"] == "suja"
    assert data["numero"] == 104
    print("\n Teste de Atualização de Mesa: OK")

def test_deletar_mesa(client: TestClient):
    """Testa se conseguimos deletar uma mesa."""
    # 1. Cria uma mesa para deletar
    response_criacao = client.post("/mesas/", json={"numero": 105, "capacidade": 3})
    mesa_id = response_criacao.json()["id"]

    # 2. Deleta a mesa
    response_delete = client.delete(f"/mesas/{mesa_id}")
    assert response_delete.status_code == 200

    # 3. Verifica se a mesa realmente foi removida
    response_get = client.get(f"/mesas/{mesa_id}")
    assert response_get.status_code == 404 # Esperamos um erro "Não Encontrado"
    print(" Teste de Deleção de Mesa: OK")

def test_buscar_mesa_inexistente(client: TestClient):
    """Testa se a API retorna 404 ao buscar uma mesa que não existe."""
    response = client.get("/mesas/99999") # coloca Um ID q não existe
    assert response.status_code == 404
    print(" Teste de Erro 404 (Buscar): OK")