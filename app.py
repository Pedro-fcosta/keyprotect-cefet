from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime
import os
import csv






app = Flask(__name__)
app.secret_key = "chave_secreta_controle_chaves"


DATABASE = "database.db"


# =========================
# CONEXÃO COM O BANCO
# =========================

def conectar_banco():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_tabelas():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            curso_setor TEXT,
            telefone TEXT,
            criado_em TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            local TEXT NOT NULL,
            descricao TEXT,
            status TEXT NOT NULL DEFAULT 'Disponível',
            criado_em TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            chave_id INTEGER NOT NULL,
            data_retirada TEXT NOT NULL,
            data_devolucao TEXT,
            status TEXT NOT NULL DEFAULT 'Em aberto',
            observacao TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (chave_id) REFERENCES chaves(id)
        )
    """)

    conexao.commit()
    conexao.close()


# =========================
# ROTAS PRINCIPAIS
# =========================

@app.route("/")
def index():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    total_chaves = cursor.execute("SELECT COUNT(*) FROM chaves").fetchone()[0]
    chaves_disponiveis = cursor.execute("SELECT COUNT(*) FROM chaves WHERE status = 'Disponível'").fetchone()[0]
    chaves_retiradas = cursor.execute("SELECT COUNT(*) FROM chaves WHERE status = 'Retirada'").fetchone()[0]
    movimentos_abertos = cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE status = 'Em aberto'").fetchone()[0]

    conexao.close()

    return render_template(
        "index.html",
        total_chaves=total_chaves,
        chaves_disponiveis=chaves_disponiveis,
        chaves_retiradas=chaves_retiradas,
        movimentos_abertos=movimentos_abertos
    )


# =========================
# USUÁRIOS
# =========================

@app.route("/usuarios")
def usuarios():
    conexao = conectar_banco()
    usuarios = conexao.execute("""
        SELECT * FROM usuarios
        ORDER BY nome ASC
    """).fetchall()
    conexao.close()

    return render_template("usuarios.html", usuarios=usuarios)


@app.route("/usuarios/cadastrar", methods=["GET", "POST"])
def cadastrar_usuario():
    if request.method == "POST":
        matricula = request.form["matricula"].strip()
        nome = request.form["nome"].strip()
        curso_setor = request.form["curso_setor"].strip()
        telefone = request.form["telefone"].strip()
        criado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

        if not matricula or not nome:
            flash("Matrícula e nome são obrigatórios.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        conexao = conectar_banco()

        try:
            conexao.execute("""
                INSERT INTO usuarios (matricula, nome, curso_setor, telefone, criado_em)
                VALUES (?, ?, ?, ?, ?)
            """, (matricula, nome, curso_setor, telefone, criado_em))

            conexao.commit()
            flash("Usuário cadastrado com sucesso.", "sucesso")

        except sqlite3.IntegrityError:
            flash("Já existe um usuário com essa matrícula.", "erro")

        finally:
            conexao.close()

        return redirect(url_for("usuarios"))

    return render_template("cadastrar_usuario.html")


# =========================
# CHAVES
# =========================

@app.route("/chaves")
def chaves():
    busca = request.args.get("busca", "").strip()

    conexao = conectar_banco()

    if busca:
        chaves = conexao.execute("""
            SELECT * FROM chaves
            WHERE codigo LIKE ? OR local LIKE ? OR status LIKE ?
            ORDER BY codigo ASC
        """, (f"%{busca}%", f"%{busca}%", f"%{busca}%")).fetchall()
    else:
        chaves = conexao.execute("""
            SELECT * FROM chaves
            ORDER BY codigo ASC
        """).fetchall()

    conexao.close()

    return render_template("chaves.html", chaves=chaves, busca=busca)


@app.route("/chaves/cadastrar", methods=["GET", "POST"])
def cadastrar_chave():
    if request.method == "POST":
        codigo = request.form["codigo"].strip()
        local = request.form["local"].strip()
        descricao = request.form["descricao"].strip()
        criado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

        if not codigo or not local:
            flash("Código da chave e local são obrigatórios.", "erro")
            return redirect(url_for("cadastrar_chave"))

        conexao = conectar_banco()

        try:
            conexao.execute("""
                INSERT INTO chaves (codigo, local, descricao, status, criado_em)
                VALUES (?, ?, ?, ?, ?)
            """, (codigo, local, descricao, "Disponível", criado_em))

            conexao.commit()
            flash("Chave cadastrada com sucesso.", "sucesso")

        except sqlite3.IntegrityError:
            flash("Já existe uma chave com esse código.", "erro")

        finally:
            conexao.close()

        return redirect(url_for("chaves"))

    return render_template("cadastrar_chave.html")


# =========================
# RETIRADA DE CHAVE
# =========================

@app.route("/retirada", methods=["GET", "POST"])
def retirada():
    conexao = conectar_banco()

    if request.method == "POST":
        matricula = request.form["matricula"].strip()
        chave_id = request.form["chave_id"]
        observacao = request.form["observacao"].strip()
        data_retirada = datetime.now().strftime("%d/%m/%Y %H:%M")

        usuario = conexao.execute("""
            SELECT * FROM usuarios
            WHERE matricula = ?
        """, (matricula,)).fetchone()

        if not usuario:
            conexao.close()
            flash("Usuário não encontrado. Cadastre o usuário antes da retirada.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        chave = conexao.execute("""
            SELECT * FROM chaves
            WHERE id = ?
        """, (chave_id,)).fetchone()

        if not chave:
            conexao.close()
            flash("Chave não encontrada.", "erro")
            return redirect(url_for("retirada"))

        if chave["status"] != "Disponível":
            conexao.close()
            flash("Essa chave não está disponível para retirada.", "erro")
            return redirect(url_for("retirada"))

        conexao.execute("""
            INSERT INTO movimentacoes (
                usuario_id, chave_id, data_retirada, data_devolucao, status, observacao
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            usuario["id"],
            chave["id"],
            data_retirada,
            None,
            "Em aberto",
            observacao
        ))

        conexao.execute("""
            UPDATE chaves
            SET status = 'Retirada'
            WHERE id = ?
        """, (chave["id"],))

        conexao.commit()
        conexao.close()

        flash("Retirada registrada com sucesso.", "sucesso")
        return redirect(url_for("index"))

    chaves_disponiveis = conexao.execute("""
        SELECT * FROM chaves
        WHERE status = 'Disponível'
        ORDER BY codigo ASC
    """).fetchall()

    conexao.close()

    return render_template("retirada.html", chaves=chaves_disponiveis)


# =========================
# DEVOLUÇÃO DE CHAVE
# =========================

@app.route("/devolucao", methods=["GET", "POST"])
def devolucao():
    conexao = conectar_banco()

    if request.method == "POST":
        movimentacao_id = request.form["movimentacao_id"]
        data_devolucao = datetime.now().strftime("%d/%m/%Y %H:%M")

        movimentacao = conexao.execute("""
            SELECT * FROM movimentacoes
            WHERE id = ? AND status = 'Em aberto'
        """, (movimentacao_id,)).fetchone()

        if not movimentacao:
            conexao.close()
            flash("Movimentação em aberto não encontrada.", "erro")
            return redirect(url_for("devolucao"))

        conexao.execute("""
            UPDATE movimentacoes
            SET data_devolucao = ?, status = 'Finalizada'
            WHERE id = ?
        """, (data_devolucao, movimentacao_id))

        conexao.execute("""
            UPDATE chaves
            SET status = 'Disponível'
            WHERE id = ?
        """, (movimentacao["chave_id"],))

        conexao.commit()
        conexao.close()

        flash("Devolução registrada com sucesso.", "sucesso")
        return redirect(url_for("index"))

    movimentacoes_abertas = conexao.execute("""
        SELECT 
            movimentacoes.id,
            movimentacoes.data_retirada,
            usuarios.nome,
            usuarios.matricula,
            chaves.codigo,
            chaves.local
        FROM movimentacoes
        JOIN usuarios ON movimentacoes.usuario_id = usuarios.id
        JOIN chaves ON movimentacoes.chave_id = chaves.id
        WHERE movimentacoes.status = 'Em aberto'
        ORDER BY movimentacoes.data_retirada DESC
    """).fetchall()

    conexao.close()

    return render_template("devolucao.html", movimentacoes=movimentacoes_abertas)


# =========================
# HISTÓRICO
# =========================

@app.route("/historico")
def historico():
    busca = request.args.get("busca", "").strip()

    conexao = conectar_banco()

    if busca:
        movimentacoes = conexao.execute("""
            SELECT 
                movimentacoes.id,
                movimentacoes.data_retirada,
                movimentacoes.data_devolucao,
                movimentacoes.status,
                movimentacoes.observacao,
                usuarios.nome,
                usuarios.matricula,
                chaves.codigo,
                chaves.local
            FROM movimentacoes
            JOIN usuarios ON movimentacoes.usuario_id = usuarios.id
            JOIN chaves ON movimentacoes.chave_id = chaves.id
            WHERE usuarios.nome LIKE ?
               OR usuarios.matricula LIKE ?
               OR chaves.codigo LIKE ?
               OR chaves.local LIKE ?
               OR movimentacoes.status LIKE ?
            ORDER BY movimentacoes.id DESC
        """, (
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%"
        )).fetchall()
    else:
        movimentacoes = conexao.execute("""
            SELECT 
                movimentacoes.id,
                movimentacoes.data_retirada,
                movimentacoes.data_devolucao,
                movimentacoes.status,
                movimentacoes.observacao,
                usuarios.nome,
                usuarios.matricula,
                chaves.codigo,
                chaves.local
            FROM movimentacoes
            JOIN usuarios ON movimentacoes.usuario_id = usuarios.id
            JOIN chaves ON movimentacoes.chave_id = chaves.id
            ORDER BY movimentacoes.id DESC
        """).fetchall()

    conexao.close()

    return render_template("historico.html", movimentacoes=movimentacoes, busca=busca)


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    conexao = conectar_banco()

    total_chaves = conexao.execute("""
        SELECT COUNT(*) FROM chaves
    """).fetchone()[0]

    chaves_disponiveis = conexao.execute("""
        SELECT COUNT(*) FROM chaves
        WHERE status = 'Disponível'
    """).fetchone()[0]

    chaves_retiradas = conexao.execute("""
        SELECT COUNT(*) FROM chaves
        WHERE status = 'Retirada'
    """).fetchone()[0]

    total_usuarios = conexao.execute("""
        SELECT COUNT(*) FROM usuarios
    """).fetchone()[0]

    total_movimentacoes = conexao.execute("""
        SELECT COUNT(*) FROM movimentacoes
    """).fetchone()[0]

    movimentos_abertos = conexao.execute("""
        SELECT COUNT(*) FROM movimentacoes
        WHERE status = 'Em aberto'
    """).fetchone()[0]

    ultimas_movimentacoes = conexao.execute("""
        SELECT 
            movimentacoes.id,
            movimentacoes.data_retirada,
            movimentacoes.data_devolucao,
            movimentacoes.status,
            usuarios.nome,
            usuarios.matricula,
            chaves.codigo,
            chaves.local
        FROM movimentacoes
        JOIN usuarios ON movimentacoes.usuario_id = usuarios.id
        JOIN chaves ON movimentacoes.chave_id = chaves.id
        ORDER BY movimentacoes.id DESC
        LIMIT 5
    """).fetchall()

    chaves_mais_utilizadas = conexao.execute("""
        SELECT 
            chaves.codigo,
            chaves.local,
            COUNT(movimentacoes.id) AS total_usos
        FROM movimentacoes
        JOIN chaves ON movimentacoes.chave_id = chaves.id
        GROUP BY chaves.id
        ORDER BY total_usos DESC
        LIMIT 5
    """).fetchall()

    usuarios_mais_ativos = conexao.execute("""
        SELECT 
            usuarios.nome,
            usuarios.matricula,
            COUNT(movimentacoes.id) AS total_retiradas
        FROM movimentacoes
        JOIN usuarios ON movimentacoes.usuario_id = usuarios.id
        GROUP BY usuarios.id
        ORDER BY total_retiradas DESC
        LIMIT 5
    """).fetchall()

    movimentacoes_abertas_lista = conexao.execute("""
        SELECT 
            movimentacoes.id,
            movimentacoes.data_retirada,
            usuarios.nome,
            usuarios.matricula,
            chaves.codigo,
            chaves.local
        FROM movimentacoes
        JOIN usuarios ON movimentacoes.usuario_id = usuarios.id
        JOIN chaves ON movimentacoes.chave_id = chaves.id
        WHERE movimentacoes.status = 'Em aberto'
    """).fetchall()

    chave_mais_tempo_aberta = None
    maior_tempo_aberto = None

    for mov in movimentacoes_abertas_lista:
        data_retirada = datetime.strptime(mov["data_retirada"], "%d/%m/%Y %H:%M")
        tempo_aberto = datetime.now() - data_retirada

        if maior_tempo_aberto is None or tempo_aberto > maior_tempo_aberto:
            maior_tempo_aberto = tempo_aberto
            chave_mais_tempo_aberta = dict(mov)
            chave_mais_tempo_aberta["dias_aberto"] = tempo_aberto.days
            chave_mais_tempo_aberta["horas_aberto"] = tempo_aberto.seconds // 3600

    conexao.close()

    return render_template(
        "dashboard.html",
        total_chaves=total_chaves,
        chaves_disponiveis=chaves_disponiveis,
        chaves_retiradas=chaves_retiradas,
        total_usuarios=total_usuarios,
        total_movimentacoes=total_movimentacoes,
        movimentos_abertos=movimentos_abertos,
        ultimas_movimentacoes=ultimas_movimentacoes,
        chave_mais_tempo_aberta=chave_mais_tempo_aberta,
        chaves_mais_utilizadas=chaves_mais_utilizadas,
        usuarios_mais_ativos=usuarios_mais_ativos
    )


# =========================
# EXPORTAÇÃO CSV
# =========================

@app.route("/exportar-historico")
def exportar_historico():
    conexao = conectar_banco()

    movimentacoes = conexao.execute("""
        SELECT 
            movimentacoes.id,
            movimentacoes.data_retirada,
            movimentacoes.data_devolucao,
            movimentacoes.status,
            movimentacoes.observacao,
            usuarios.nome,
            usuarios.matricula,
            usuarios.curso_setor,
            chaves.codigo,
            chaves.local,
            chaves.descricao
        FROM movimentacoes
        JOIN usuarios ON movimentacoes.usuario_id = usuarios.id
        JOIN chaves ON movimentacoes.chave_id = chaves.id
        ORDER BY movimentacoes.id DESC
    """).fetchall()

    conexao.close()

    pasta_exports = "exports"

    if not os.path.exists(pasta_exports):
        os.makedirs(pasta_exports)

    caminho_arquivo = os.path.join(pasta_exports, "historico_chaves.csv")

    with open(caminho_arquivo, mode="w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")

        escritor.writerow([
            "ID",
            "Código da chave",
            "Local",
            "Descrição da chave",
            "Responsável",
            "Matrícula",
            "Curso/Setor",
            "Data retirada",
            "Data devolução",
            "Status",
            "Observação"
        ])

        for mov in movimentacoes:
            escritor.writerow([
                mov["id"],
                mov["codigo"],
                mov["local"],
                mov["descricao"],
                mov["nome"],
                mov["matricula"],
                mov["curso_setor"],
                mov["data_retirada"],
                mov["data_devolucao"] or "",
                mov["status"],
                mov["observacao"] or ""
            ])

    return send_file(
        caminho_arquivo,
        as_attachment=True,
        download_name="historico_chaves.csv"
    )


# =========================
# INICIAR SISTEMA
# =========================

if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)