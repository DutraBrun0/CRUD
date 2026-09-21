from pathlib import Path
import sqlite3

from flask import Flask, flash, g, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "crud.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "chave-de-desenvolvimento"
app.config["DATABASE"] = DATABASE


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL DEFAULT '',
            preco REAL NOT NULL CHECK (preco >= 0),
            criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def validar_produto(form):
    nome = form.get("nome", "").strip()
    descricao = form.get("descricao", "").strip()
    preco_texto = form.get("preco", "").strip().replace(",", ".")

    if not nome:
        return None, "O nome é obrigatório."

    try:
        preco = float(preco_texto)
    except ValueError:
        return None, "Informe um preço válido."

    if preco < 0:
        return None, "O preço não pode ser negativo."

    return {"nome": nome, "descricao": descricao, "preco": preco}, None


@app.route("/")
def index():
    produtos = get_db().execute(
        "SELECT id, nome, descricao, preco FROM produtos ORDER BY id DESC"
    ).fetchall()
    return render_template("index.html", produtos=produtos)


@app.route("/novo", methods=("GET", "POST"))
def novo():
    if request.method == "POST":
        produto, erro = validar_produto(request.form)
        if erro:
            flash(erro, "erro")
            return render_template("form.html", produto=request.form, titulo="Novo produto")

        db = get_db()
        db.execute(
            "INSERT INTO produtos (nome, descricao, preco) VALUES (?, ?, ?)",
            (produto["nome"], produto["descricao"], produto["preco"]),
        )
        db.commit()
        flash("Produto criado com sucesso.", "sucesso")
        return redirect(url_for("index"))

    return render_template("form.html", produto=None, titulo="Novo produto")


@app.route("/editar/<int:produto_id>", methods=("GET", "POST"))
def editar(produto_id):
    db = get_db()
    produto = db.execute(
        "SELECT id, nome, descricao, preco FROM produtos WHERE id = ?", (produto_id,)
    ).fetchone()

    if produto is None:
        flash("Produto não encontrado.", "erro")
        return redirect(url_for("index"))

    if request.method == "POST":
        dados, erro = validar_produto(request.form)
        if erro:
            flash(erro, "erro")
            return render_template(
                "form.html", produto=request.form, titulo="Editar produto"
            )

        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ? WHERE id = ?",
            (dados["nome"], dados["descricao"], dados["preco"], produto_id),
        )
        db.commit()
        flash("Produto atualizado com sucesso.", "sucesso")
        return redirect(url_for("index"))

    return render_template("form.html", produto=produto, titulo="Editar produto")


@app.post("/excluir/<int:produto_id>")
def excluir(produto_id):
    db = get_db()
    cursor = db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()

    if cursor.rowcount:
        flash("Produto excluído com sucesso.", "sucesso")
    else:
        flash("Produto não encontrado.", "erro")
    return redirect(url_for("index"))


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)
