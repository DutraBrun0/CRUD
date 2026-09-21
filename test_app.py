import pytest

from app import app


@pytest.fixture()
def client(tmp_path):
    app.config.update(
        TESTING=True,
        DATABASE=tmp_path / "test.db",
    )
    with app.app_context():
        from app import init_db

        init_db()
    with app.test_client() as test_client:
        yield test_client


def test_crud_produto(client):
    resposta = client.post(
        "/novo",
        data={"nome": "Notebook", "descricao": "Modelo básico", "preco": "2500,00"},
        follow_redirects=True,
    )
    assert resposta.status_code == 200
    assert "Notebook" in resposta.get_data(as_text=True)

    resposta = client.post(
        "/editar/1",
        data={"nome": "Notebook atualizado", "descricao": "", "preco": "2600"},
        follow_redirects=True,
    )
    assert "Notebook atualizado" in resposta.get_data(as_text=True)

    resposta = client.post("/excluir/1", follow_redirects=True)
    assert "Nenhum produto cadastrado." in resposta.get_data(as_text=True)


def test_rejeita_preco_negativo(client):
    resposta = client.post(
        "/novo",
        data={"nome": "Produto inválido", "descricao": "", "preco": "-1"},
    )
    assert resposta.status_code == 200
    assert "não pode ser negativo" in resposta.get_data(as_text=True)
