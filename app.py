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
            tipo_usuario TEXT,
            curso_setor TEXT,
            telefone TEXT,
            criado_em TEXT NOT NULL
        )
    """)

    # Garante que bancos antigos também tenham a coluna tipo_usuario
    colunas_usuarios = cursor.execute("PRAGMA table_info(usuarios)").fetchall()
    nomes_colunas = [coluna[1] for coluna in colunas_usuarios]

    if "tipo_usuario" not in nomes_colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN tipo_usuario TEXT")

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
            usuario_devolucao_id INTEGER,
            data_retirada TEXT NOT NULL,
            data_devolucao TEXT,
            status TEXT NOT NULL DEFAULT 'Em aberto',
            observacao TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (usuario_devolucao_id) REFERENCES usuarios(id),
            FOREIGN KEY (chave_id) REFERENCES chaves(id)
        )
    """)

    # Garante que bancos antigos também tenham a coluna usuario_devolucao_id
    colunas_movimentacoes = cursor.execute("PRAGMA table_info(movimentacoes)").fetchall()
    nomes_colunas_mov = [coluna[1] for coluna in colunas_movimentacoes]

    if "usuario_devolucao_id" not in nomes_colunas_mov:
        cursor.execute("ALTER TABLE movimentacoes ADD COLUMN usuario_devolucao_id INTEGER")


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
        tipo_usuario = request.form["tipo_usuario"].strip()
        curso_setor = request.form.get("curso_setor", "").strip()
        telefone = request.form["telefone"].strip()
        criado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

        if not matricula or not nome or not tipo_usuario:
            flash("Matrícula, nome e tipo de usuário são obrigatórios.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        if tipo_usuario == "Aluno" and not curso_setor:
            flash("Para aluno, o curso é obrigatório.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        if tipo_usuario == "Professor" and not curso_setor:
            flash("Para professor, o tipo de ensino é obrigatório.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        if tipo_usuario in ["Técnico", "Funcionário"]:
            curso_setor = ""

        conexao = conectar_banco()

        try:
            conexao.execute("""
                INSERT INTO usuarios (
                    matricula, nome, tipo_usuario, curso_setor, telefone, criado_em
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                matricula,
                nome,
                tipo_usuario,
                curso_setor,
                telefone,
                criado_em
            ))

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
        local = request.form["local"].strip()
        descricao = request.form["descricao"].strip()
        criado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

        if not local:
            flash("Local da chave é obrigatório.", "erro")
            return redirect(url_for("cadastrar_chave"))

        conexao = conectar_banco()
        cursor = conexao.cursor()

        try:
            # Primeiro cadastra a chave sem código definitivo
            cursor.execute("""
                INSERT INTO chaves (codigo, local, descricao, status, criado_em)
                VALUES (?, ?, ?, ?, ?)
            """, ("TEMP", local, descricao, "Disponível", criado_em))

            chave_id = cursor.lastrowid

            # Depois gera o código sequencial baseado no ID automático
            codigo = f"CH-{chave_id:03d}"

            cursor.execute("""
                UPDATE chaves
                SET codigo = ?
                WHERE id = ?
            """, (codigo, chave_id))

            conexao.commit()
            flash(f"Chave cadastrada com sucesso. Código gerado: {codigo}", "sucesso")

        except sqlite3.IntegrityError:
            flash("Erro ao cadastrar chave. Tente novamente.", "erro")

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

    # Essa parte fica FORA do if POST.
    # Ela roda quando a página é aberta pelo navegador usando GET.
    chaves = conexao.execute("""
        SELECT * FROM chaves
        ORDER BY codigo ASC
    """).fetchall()

    conexao.close()

    return render_template("retirada.html", chaves=chaves)

# =========================
# DEVOLUÇÃO DE CHAVE
# =========================

@app.route("/devolucao", methods=["GET", "POST"])
def devolucao():
    conexao = conectar_banco()

    if request.method == "POST":
        movimentacao_id = request.form["movimentacao_id"]
        matricula_devolucao = request.form["matricula_devolucao"].strip()
        confirmar_devolucao = request.form.get("confirmar_devolucao", "nao")
        data_devolucao = datetime.now().strftime("%d/%m/%Y %H:%M")

        if not matricula_devolucao:
            conexao.close()
            flash("Informe a matrícula de quem está devolvendo a chave.", "erro")
            return redirect(url_for("devolucao"))

        movimentacao = conexao.execute("""
            SELECT 
                movimentacoes.*,
                usuarios.nome AS nome_retirada,
                usuarios.matricula AS matricula_retirada,
                chaves.codigo,
                chaves.local
            FROM movimentacoes
            JOIN usuarios ON movimentacoes.usuario_id = usuarios.id
            JOIN chaves ON movimentacoes.chave_id = chaves.id
            WHERE movimentacoes.id = ? AND movimentacoes.status = 'Em aberto'
        """, (movimentacao_id,)).fetchone()

        if not movimentacao:
            conexao.close()
            flash("Movimentação em aberto não encontrada.", "erro")
            return redirect(url_for("devolucao"))

        usuario_devolucao = conexao.execute("""
            SELECT * FROM usuarios
            WHERE matricula = ?
        """, (matricula_devolucao,)).fetchone()

        if not usuario_devolucao:
            conexao.close()
            flash("Usuário não encontrado. Cadastre o usuário antes de registrar a devolução.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        mesma_pessoa = usuario_devolucao["id"] == movimentacao["usuario_id"]

        if not mesma_pessoa and confirmar_devolucao != "sim":
            conexao.close()
            return render_template(
                "confirmar_devolucao.html",
                movimentacao=movimentacao,
                usuario_devolucao=usuario_devolucao
            )

        conexao.execute("""
            UPDATE movimentacoes
            SET 
                data_devolucao = ?, 
                status = 'Finalizada',
                usuario_devolucao_id = ?
            WHERE id = ?
        """, (
            data_devolucao,
            usuario_devolucao["id"],
            movimentacao_id
        ))

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

    sql_base = """
        SELECT 
            movimentacoes.id,
            movimentacoes.data_retirada,
            movimentacoes.data_devolucao,
            movimentacoes.status,
            movimentacoes.observacao,

            usuario_retirada.nome AS nome_retirada,
            usuario_retirada.matricula AS matricula_retirada,

            usuario_devolucao.nome AS nome_devolucao,
            usuario_devolucao.matricula AS matricula_devolucao,

            chaves.codigo,
            chaves.local
        FROM movimentacoes
        JOIN usuarios AS usuario_retirada 
            ON movimentacoes.usuario_id = usuario_retirada.id
        LEFT JOIN usuarios AS usuario_devolucao 
            ON movimentacoes.usuario_devolucao_id = usuario_devolucao.id
        JOIN chaves 
            ON movimentacoes.chave_id = chaves.id
    """

    if busca:
        movimentacoes = conexao.execute(sql_base + """
            WHERE usuario_retirada.nome LIKE ?
               OR usuario_retirada.matricula LIKE ?
               OR usuario_devolucao.nome LIKE ?
               OR usuario_devolucao.matricula LIKE ?
               OR chaves.codigo LIKE ?
               OR chaves.local LIKE ?
               OR movimentacoes.status LIKE ?
            ORDER BY movimentacoes.id DESC
        """, (
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%"
        )).fetchall()
    else:
        movimentacoes = conexao.execute(sql_base + """
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