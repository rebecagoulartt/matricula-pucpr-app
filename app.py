import os
from flask import Flask, render_template, request, redirect, url_for
import pyodbc

app = Flask(__name__)


def get_connection():
    """
    Procura a connection string configurada no App Service.
    O Azure expoe cadeias de conexao do tipo SQLAzure como variaveis
    de ambiente no formato SQLCONNSTR_<nome>.
    """
    conn_str = (
        os.environ.get("SQLCONNSTR_DefaultConnection")
        or os.environ.get("DefaultConnection")
    )
    if not conn_str:
        raise RuntimeError(
            "Connection string 'DefaultConnection' nao encontrada nas "
            "variaveis de ambiente."
        )
    return pyodbc.connect(conn_str)


@app.route("/")
def index():
    db_status = "OK"
    rows = []
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, curso, status, data_criacao FROM matriculas "
            "ORDER BY id DESC"
        )
        rows = cursor.fetchall()
        conn.close()
    except Exception as exc:  # noqa: BLE001
        db_status = f"Erro ao conectar/consultar: {exc}"

    return render_template("index.html", rows=rows, db_status=db_status)


@app.route("/matricula", methods=["POST"])
def nova_matricula():
    nome = request.form.get("nome", "").strip()
    curso = request.form.get("curso", "").strip()

    if not nome or not curso:
        return redirect(url_for("index"))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO matriculas (nome, curso, status) "
            "VALUES (?, ?, ?)",
            (nome, curso, "Pendente"),
        )
        conn.commit()
        conn.close()
    except Exception as exc:  # noqa: BLE001
        return f"Erro ao inserir matricula: {exc}", 500

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
