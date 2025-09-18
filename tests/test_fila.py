# back/tests/test_fila.py
from fastapi.testclient import TestClient


def test_adicionar_cliente_a_fila(client: TestClient):
    """Testa se conseguimos adicionar um cliente à fila e se ele aparece na listagem."""
    response = client.post("/fila/", json={"nome_cliente": "Familia Teste", "tamanho_grupo": 4})
    assert response.status_code == 201
    data = response.json()
    assert data["nome_cliente"] == "Familia Teste"
    assert data["status"] == "aguardando"

    # Verifica se o cliente aparece na lista da fila
    response_lista = client.get("/fila/")
    assert response_lista.status_code == 200
    assert any(c["nome_cliente"] == "Familia Teste" for c in response_lista.json())

def test_atribuir_cliente_a_mesa_simples(client: TestClient):
    """Testa o cenário simples de atender um cliente numa mesa disponível."""
    # 1. Cria uma mesa disponível
    mesa_response = client.post("/mesas/", json={"numero": 201, "capacidade": 5})
    mesa_id = mesa_response.json()["id"]

    # 2. Adiciona um cliente à fila
    client.post("/fila/", json={"nome_cliente": "Cliente a ser Atendido", "tamanho_grupo": 3})

    # 3. Tenta atribuir o cliente à mesa
    response_atribuicao = client.post(f"/mesas/{mesa_id}/atribuir-proximo")
    
    # 4. Verifica os resultados
    assert response_atribuicao.status_code == 200
    mesa_atualizada = response_atribuicao.json()
    assert mesa_atualizada["status"] == "ocupada"
    assert mesa_atualizada["cliente_atual"] == "Cliente a ser Atendido"

    # 5. Verifica se a fila ficou vazia
    response_fila = client.get("/fila/")
    fila_atual = response_fila.json()
    assert len(fila_atual) == 0



def test_cancelar_cliente_fila(client: TestClient):
    """Testa se podemos cancelar um cliente e se ele some da fila de espera."""
    # Adiciona um cliente que vamos cancelar
    response_cliente = client.post("/fila/", json={"nome_cliente": "Cliente Desistente", "tamanho_grupo": 2})
    cliente_id = response_cliente.json()["id"]

    # Cancela o cliente usando a API de atualização
    response_update = client.put(f"/fila/{cliente_id}", json={"status": "cancelado"})
    assert response_update.status_code == 200
    assert response_update.json()["status"] == "cancelado"

    # Verifica se o cliente já não aparece na fila de espera (que só mostra 'aguardando')
    response_fila = client.get("/fila/")
    assert response_fila.status_code == 200
    assert not any(c["id"] == cliente_id for c in response_fila.json())
    print("\n Teste de Cancelamento de Cliente: OK")


def test_atender_proximo_sem_mesas_disponiveis(client: TestClient):
    """Testa se a API retorna um erro quando não há mesas para atender."""
    # Garante que a fila não está vazia
    client.post("/fila/", json={"nome_cliente": "Cliente Sem Sorte", "tamanho_grupo": 4})

 
    
    # Tenta atender o próximo
    response = client.post("/fila/atender-proximo")

    # Verifica se recebemos o erro esperado (409 Conflict)
    assert response.status_code == 409
    assert "Não há mesas" in response.json()["detail"]
    print(" Teste de Atendimento Sem Mesas: OK")


def test_atender_grupo_grande_combinando_mesas(client: TestClient):
    """Testa a lógica inteligente de juntar mesas para um grupo grande."""
    # 1. Cria duas mesas pequenas
    client.post("/mesas/", json={"numero": 301, "capacidade": 4})
    client.post("/mesas/", json={"numero": 302, "capacidade": 4})

    # 2. Adiciona um grupo grande à fila
    client.post("/fila/", json={"nome_cliente": "Grupo Grande", "tamanho_grupo": 8})

    # 3. Tenta atender
    response_atendimento = client.post("/fila/atender-proximo")
    assert response_atendimento.status_code == 200
    assert "Mesa(s) 301, 302" in response_atendimento.json()["detail"]

    # 4. Verifica se as duas mesas estão agora ocupadas pelo mesmo cliente
    response_mesas = client.get("/mesas/")
    mesas = response_mesas.json()
    mesa1 = next(m for m in mesas if m["numero"] == 301)
    mesa2 = next(m for m in mesas if m["numero"] == 302)

    assert mesa1["status"] == "ocupada"
    assert mesa2["status"] == "ocupada"
    assert mesa1["cliente_atual"] == "Grupo Grande"
    assert mesa2["cliente_atual"] == "Grupo Grande"
    
    # 5. Verifica se a fila ficou vazia
    response_fila = client.get("/fila/")
    assert len(response_fila.json()) == 0
    print(" Teste de Atendimento com Mesas Combinadas: OK")