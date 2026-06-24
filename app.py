from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime, timedelta
import os
import csv
import re
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from werkzeug.security import generate_password_hash, check_password_hash





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
            pin_hash TEXT,
            criado_em TEXT NOT NULL
        )
    """)

    # Garante que bancos antigos também tenham a coluna tipo_usuario
    colunas_usuarios = cursor.execute("PRAGMA table_info(usuarios)").fetchall()
    nomes_colunas = [coluna[1] for coluna in colunas_usuarios]

    if "tipo_usuario" not in nomes_colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN tipo_usuario TEXT")

    # Garante que bancos antigos também tenham a coluna pin_hash
    colunas_usuarios = cursor.execute("PRAGMA table_info(usuarios)").fetchall()
    nomes_colunas = [coluna[1] for coluna in colunas_usuarios]

    if "tipo_usuario" not in nomes_colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN tipo_usuario TEXT")

    if "pin_hash" not in nomes_colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN pin_hash TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            local TEXT NOT NULL,
            descricao TEXT,
            status TEXT NOT NULL DEFAULT 'Disponível',
            criado_em TEXT NOT NULL,
            tipo TEXT DEFAULT 'sala_aula',
            andar INTEGER
        )
    """)


    # Garante que bancos antigos também tenham as colunas tipo e andar
    colunas_chaves = cursor.execute("PRAGMA table_info(chaves)").fetchall()
    nomes_colunas_chaves = [coluna[1] for coluna in colunas_chaves]

    if "tipo" not in nomes_colunas_chaves:
        cursor.execute("ALTER TABLE chaves ADD COLUMN tipo TEXT DEFAULT 'sala_aula'")

    if "andar" not in nomes_colunas_chaves:
        cursor.execute("ALTER TABLE chaves ADD COLUMN andar INTEGER")


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


def formatar_telefone(telefone):
    telefone = telefone or ""

    # Remove tudo que não for número
    numeros = re.sub(r"\D", "", telefone)

    # Celular com 11 dígitos: DDD + 9 dígitos
    # Exemplo: 21985130419 -> (21) 98513-0419
    if len(numeros) == 11:
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"

    # Telefone com 10 dígitos: DDD + 8 dígitos
    # Exemplo: 2198513041 -> (21) 9851-3041
    if len(numeros) == 10:
        return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"

    # Se estiver vazio, deixa vazio
    if len(numeros) == 0:
        return ""

    # Se tiver quantidade estranha, retorna como digitado
    return telefone.strip()


def parse_data_sistema(valor):
    if not valor:
        return None

    valor = str(valor).strip()

    formatos = [
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M"
    ]

    for formato in formatos:
        try:
            return datetime.strptime(valor, formato)
        except ValueError:
            continue

    return None


def formatar_duracao(segundos):
    if segundos is None:
        return "-"

    segundos = int(segundos)

    if segundos < 0:
        segundos = 0

    dias = segundos // 86400
    horas = (segundos % 86400) // 3600
    minutos = (segundos % 3600) // 60

    partes = []

    if dias > 0:
        partes.append(f"{dias} dia(s)")
    if horas > 0:
        partes.append(f"{horas} hora(s)")
    if minutos > 0:
        partes.append(f"{minutos} min")

    if not partes:
        return "0 min"

    return " ".join(partes[:3])


def formatar_data_exibicao(valor):
    data = parse_data_sistema(valor)

    if not data:
        return valor if valor else "-"

    return data.strftime("%d/%m/%Y %H:%M")


def obter_periodo_dashboard(periodo):
    agora = datetime.now()

    periodos = {
        "1d": {
            "inicio": agora - timedelta(days=1),
            "label": "Últimas 24 horas"
        },
        "7d": {
            "inicio": agora - timedelta(days=7),
            "label": "Últimos 7 dias"
        },
        "1m": {
            "inicio": agora - timedelta(days=30),
            "label": "Últimos 30 dias"
        },
        "6m": {
            "inicio": agora - timedelta(days=180),
            "label": "Últimos 6 meses"
        }
    }

    return periodos.get(periodo, periodos["6m"])


def obter_dados_dashboard(periodo="6m"):
    conexao = conectar_banco()
    agora = datetime.now()

    dados_periodo = obter_periodo_dashboard(periodo)
    data_inicio = dados_periodo["inicio"]
    periodo_label = dados_periodo["label"]

    total_chaves = conexao.execute("""
        SELECT COUNT(*) AS total
        FROM chaves
    """).fetchone()["total"]

    chaves_disponiveis = conexao.execute("""
        SELECT COUNT(*) AS total
        FROM chaves
        WHERE status = 'Disponível'
    """).fetchone()["total"]

    chaves_retiradas = conexao.execute("""
        SELECT COUNT(*) AS total
        FROM chaves
        WHERE status = 'Retirada'
    """).fetchone()["total"]

    movimentos_abertos = conexao.execute("""
        SELECT COUNT(*) AS total
        FROM movimentacoes
        WHERE status = 'Em aberto'
    """).fetchone()["total"]

    total_usuarios = conexao.execute("""
        SELECT COUNT(*) AS total
        FROM usuarios
    """).fetchone()["total"]

    movimentacoes = conexao.execute("""
        SELECT
            m.id,
            m.data_retirada,
            m.data_devolucao,
            m.status,
            m.observacao,

            c.codigo,
            c.local,

            u.nome AS responsavel,
            u.matricula AS matricula_retirada

        FROM movimentacoes m
        JOIN chaves c ON c.id = m.chave_id
        JOIN usuarios u ON u.id = m.usuario_id

        ORDER BY m.id DESC
    """).fetchall()

    conexao.close()

    movimentacoes_periodo = []

    for mov in movimentacoes:
        data_retirada = parse_data_sistema(mov["data_retirada"])

        if data_retirada and data_retirada >= data_inicio:
            movimentacoes_periodo.append(mov)

    total_movimentacoes = len(movimentacoes_periodo)

    tempos_devolucao = []
    retiradas_por_dia = defaultdict(int)

    contador_chaves = defaultdict(int)
    contador_usuarios = defaultdict(int)

    for mov in movimentacoes_periodo:
        data_retirada = parse_data_sistema(mov["data_retirada"])
        data_devolucao = parse_data_sistema(mov["data_devolucao"])

        if data_retirada:
            retiradas_por_dia[data_retirada.date()] += 1

        if data_retirada and data_devolucao:
            diferenca = data_devolucao - data_retirada
            tempos_devolucao.append(diferenca.total_seconds())

        label_chave = f"{mov['codigo']} - {mov['local']}"
        contador_chaves[label_chave] += 1

        contador_usuarios[mov["responsavel"]] += 1

    if tempos_devolucao:
        media_segundos = sum(tempos_devolucao) / len(tempos_devolucao)
        tempo_medio_devolucao = formatar_duracao(media_segundos)
    else:
        tempo_medio_devolucao = "-"

    top_chaves = sorted(
        contador_chaves.items(),
        key=lambda item: item[1],
        reverse=True
    )[:5]

    top_usuarios = sorted(
        contador_usuarios.items(),
        key=lambda item: item[1],
        reverse=True
    )[:5]

    top_chaves_labels = [item[0] for item in top_chaves]
    top_chaves_valores = [item[1] for item in top_chaves]

    top_usuarios_labels = [item[0] for item in top_usuarios]
    top_usuarios_valores = [item[1] for item in top_usuarios]

    chave_mais_utilizada = top_chaves_labels[0] if top_chaves_labels else "-"
    usuario_mais_ativo = top_usuarios_labels[0] if top_usuarios_labels else "-"

    dias_ordenados = sorted(retiradas_por_dia.keys())

    retiradas_por_dia_labels = [
        dia.strftime("%d/%m") for dia in dias_ordenados
    ]

    retiradas_por_dia_valores = [
        retiradas_por_dia[dia] for dia in dias_ordenados
    ]

    status_chaves_labels = ["Disponíveis", "Retiradas"]
    status_chaves_valores = [chaves_disponiveis, chaves_retiradas]

    retiradas_abertas = []

    for mov in movimentacoes:
        data_retirada = parse_data_sistema(mov["data_retirada"])

        if mov["status"] == "Em aberto" and data_retirada:
            tempo_aberto_segundos = (agora - data_retirada).total_seconds()

            retiradas_abertas.append({
                "codigo": mov["codigo"],
                "local": mov["local"],
                "responsavel": mov["responsavel"],
                "data_retirada": data_retirada.strftime("%d/%m/%Y %H:%M"),
                "tempo_aberto_segundos": tempo_aberto_segundos,
                "tempo_aberto_formatado": formatar_duracao(tempo_aberto_segundos)
            })

    retiradas_abertas = sorted(
        retiradas_abertas,
        key=lambda item: item["tempo_aberto_segundos"],
        reverse=True
    )

    devolucoes_atrasadas = sum(
        1 for item in retiradas_abertas
        if item["tempo_aberto_segundos"] > 24 * 3600
    )

    chave_mais_tempo_sem_devolucao = retiradas_abertas[0] if retiradas_abertas else None

    ultimas_movimentacoes = []

    for mov in movimentacoes_periodo[:6]:
        ultimas_movimentacoes.append({
            "codigo": mov["codigo"],
            "local": mov["local"],
            "responsavel": mov["responsavel"],
            "retirada": formatar_data_exibicao(mov["data_retirada"]),
            "status": mov["status"]
        })

    return {
        "periodo": periodo,
        "periodo_label": periodo_label,

        "total_chaves": total_chaves,
        "chaves_disponiveis": chaves_disponiveis,
        "chaves_retiradas": chaves_retiradas,
        "movimentos_abertos": movimentos_abertos,
        "total_usuarios": total_usuarios,
        "total_movimentacoes": total_movimentacoes,
        "tempo_medio_devolucao": tempo_medio_devolucao,
        "devolucoes_atrasadas": devolucoes_atrasadas,

        "chave_mais_utilizada": chave_mais_utilizada,
        "usuario_mais_ativo": usuario_mais_ativo,
        "chave_mais_tempo_sem_devolucao": chave_mais_tempo_sem_devolucao,

        "ultimas_movimentacoes": ultimas_movimentacoes,
        "retiradas_abertas": retiradas_abertas[:5],

        "status_chaves_labels": status_chaves_labels,
        "status_chaves_valores": status_chaves_valores,

        "top_chaves_labels": top_chaves_labels,
        "top_chaves_valores": top_chaves_valores,

        "top_usuarios_labels": top_usuarios_labels,
        "top_usuarios_valores": top_usuarios_valores,

        "retiradas_por_dia_labels": retiradas_por_dia_labels,
        "retiradas_por_dia_valores": retiradas_por_dia_valores,

        "top_chaves": top_chaves,
        "top_usuarios": top_usuarios
    }


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
        telefone = formatar_telefone(request.form["telefone"])
        pin = request.form.get("pin", "").strip()
        confirmar_pin = request.form.get("confirmar_pin", "").strip()
        criado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

        if not matricula or not nome or not tipo_usuario:
            flash("Matrícula, nome e tipo de usuário são obrigatórios.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        if not pin or not confirmar_pin:
            flash("O PIN de 4 dígitos é obrigatório.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        if pin != confirmar_pin:
            flash("Os PINs digitados não conferem.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        if not pin.isdigit() or len(pin) != 4:
            flash("O PIN deve conter exatamente 4 números.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        if tipo_usuario == "Aluno" and not curso_setor:
            flash("Para aluno, o curso é obrigatório.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        if tipo_usuario == "Professor" and not curso_setor:
            flash("Para professor, o tipo de ensino é obrigatório.", "erro")
            return redirect(url_for("cadastrar_usuario"))

        if tipo_usuario in ["Técnico", "Funcionário"]:
            curso_setor = ""

        pin_hash = generate_password_hash(pin)

        conexao = conectar_banco()

        try:
            conexao.execute("""
                INSERT INTO usuarios (
                    matricula,
                    nome,
                    tipo_usuario,
                    curso_setor,
                    telefone,
                    pin_hash,
                    criado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                matricula,
                nome,
                tipo_usuario,
                curso_setor,
                telefone,
                pin_hash,
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



@app.route("/usuarios/editar/<int:usuario_id>", methods=["GET", "POST"])
def editar_usuario(usuario_id):
    conexao = conectar_banco()

    usuario = conexao.execute("""
        SELECT *
        FROM usuarios
        WHERE id = ?
    """, (usuario_id,)).fetchone()

    if not usuario:
        conexao.close()
        flash("Usuário não encontrado.", "erro")
        return redirect(url_for("usuarios"))

    if request.method == "POST":
        matricula = request.form["matricula"].strip()
        nome = request.form["nome"].strip()
        tipo_usuario = request.form["tipo_usuario"].strip()
        curso_setor = request.form.get("curso_setor", "").strip()
        telefone = formatar_telefone(request.form["telefone"])
        novo_pin = request.form.get("novo_pin", "").strip()
        confirmar_novo_pin = request.form.get("confirmar_novo_pin", "").strip()

        if not matricula or not nome or not tipo_usuario:
            conexao.close()
            flash("Matrícula, nome e tipo de usuário são obrigatórios.", "erro")
            return redirect(url_for("editar_usuario", usuario_id=usuario_id))

        if tipo_usuario == "Aluno" and not curso_setor:
            conexao.close()
            flash("Para aluno, o curso é obrigatório.", "erro")
            return redirect(url_for("editar_usuario", usuario_id=usuario_id))

        if tipo_usuario == "Professor" and not curso_setor:
            conexao.close()
            flash("Para professor, o tipo de ensino é obrigatório.", "erro")
            return redirect(url_for("editar_usuario", usuario_id=usuario_id))

        if tipo_usuario in ["Técnico", "Funcionário"]:
            curso_setor = ""

        try:
            if novo_pin or confirmar_novo_pin:
                if novo_pin != confirmar_novo_pin:
                    conexao.close()
                    flash("Os novos PINs digitados não conferem.", "erro")
                    return redirect(url_for("editar_usuario", usuario_id=usuario_id))

                if not novo_pin.isdigit() or len(novo_pin) != 4:
                    conexao.close()
                    flash("O novo PIN deve conter exatamente 4 números.", "erro")
                    return redirect(url_for("editar_usuario", usuario_id=usuario_id))

                novo_pin_hash = generate_password_hash(novo_pin)

                conexao.execute("""
                    UPDATE usuarios
                    SET matricula = ?,
                        nome = ?,
                        tipo_usuario = ?,
                        curso_setor = ?,
                        telefone = ?,
                        pin_hash = ?
                    WHERE id = ?
                """, (
                    matricula,
                    nome,
                    tipo_usuario,
                    curso_setor,
                    telefone,
                    novo_pin_hash,
                    usuario_id
                ))

            else:
                conexao.execute("""
                    UPDATE usuarios
                    SET matricula = ?,
                        nome = ?,
                        tipo_usuario = ?,
                        curso_setor = ?,
                        telefone = ?
                    WHERE id = ?
                """, (
                    matricula,
                    nome,
                    tipo_usuario,
                    curso_setor,
                    telefone,
                    usuario_id
                ))

            conexao.commit()
            flash("Usuário atualizado com sucesso.", "sucesso")

        except sqlite3.IntegrityError:
            flash("Já existe outro usuário com essa matrícula.", "erro")

        finally:
            conexao.close()

        return redirect(url_for("usuarios"))

    conexao.close()
    return render_template("editar_usuario.html", usuario=usuario)



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
        local = request.form.get("local", "").strip()
        descricao = request.form.get("descricao", "").strip()
        tipo = request.form.get("tipo", "").strip()
        andar = request.form.get("andar", "").strip()
        criado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

        if not local:
            flash("Local/Sala é obrigatório.", "erro")
            return redirect(url_for("cadastrar_chave"))

        if not tipo:
            flash("Tipo de ambiente é obrigatório.", "erro")
            return redirect(url_for("cadastrar_chave"))

        if andar:
            andar = int(andar)
        else:
            andar = None

        conexao = conectar_banco()
        cursor = conexao.cursor()

        try:
            cursor.execute("""
                INSERT INTO chaves (
                    codigo,
                    local,
                    descricao,
                    status,
                    criado_em,
                    tipo,
                    andar
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "TEMP",
                local,
                descricao,
                "Disponível",
                criado_em,
                tipo,
                andar
            ))

            chave_id = cursor.lastrowid
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



@app.route("/chaves/editar/<int:chave_id>", methods=["GET", "POST"])
def editar_chave(chave_id):
    conexao = conectar_banco()

    chave = conexao.execute("""
        SELECT *
        FROM chaves
        WHERE id = ?
    """, (chave_id,)).fetchone()

    if not chave:
        conexao.close()
        flash("Chave não encontrada.", "erro")
        return redirect(url_for("chaves"))

    if request.method == "POST":
        codigo = request.form.get("codigo", chave["codigo"]).strip().upper()
        local = request.form["local"].strip().upper()
        descricao = request.form.get("descricao", "").strip()
        status = request.form.get("status", chave["status"]).strip()
        tipo = request.form["tipo"].strip()
        andar = request.form.get("andar", "").strip()

        if not codigo or not local or not status or not tipo:
            conexao.close()
            flash("Código, local, status e tipo são obrigatórios.", "erro")
            return redirect(url_for("editar_chave", chave_id=chave_id))

        if tipo != "sala_aula":
            andar = None
        else:
            if not andar:
                conexao.close()
                flash("Para sala de aula, informe o andar.", "erro")
                return redirect(url_for("editar_chave", chave_id=chave_id))

        try:
            conexao.execute("""
                UPDATE chaves
                SET codigo = ?,
                    local = ?,
                    descricao = ?,
                    status = ?,
                    tipo = ?,
                    andar = ?
                WHERE id = ?
            """, (
                codigo,
                local,
                descricao,
                status,
                tipo,
                andar,
                chave_id
            ))

            conexao.commit()
            flash("Chave atualizada com sucesso.", "sucesso")

        except sqlite3.IntegrityError:
            flash("Já existe uma chave cadastrada com esse código.", "erro")

        finally:
            conexao.close()

        return redirect(url_for("chaves"))

    conexao.close()
    return render_template("editar_chave.html", chave=chave)



@app.route("/chaves/excluir/<int:chave_id>", methods=["POST"])
def excluir_chave(chave_id):
    conexao = conectar_banco()

    chave = conexao.execute("""
        SELECT *
        FROM chaves
        WHERE id = ?
    """, (chave_id,)).fetchone()

    if not chave:
        conexao.close()
        flash("Chave não encontrada.", "erro")
        return redirect(url_for("chaves"))

    if chave["status"] == "Retirada":
        conexao.close()
        flash("Não é possível excluir uma chave que está retirada.", "erro")
        return redirect(url_for("editar_chave", chave_id=chave_id))

    movimentacoes = conexao.execute("""
        SELECT COUNT(*) AS total
        FROM movimentacoes
        WHERE chave_id = ?
    """, (chave_id,)).fetchone()

    if movimentacoes["total"] > 0:
        conexao.close()
        flash("Essa chave possui histórico de movimentações e não pode ser excluída para preservar a rastreabilidade.", "erro")
        return redirect(url_for("editar_chave", chave_id=chave_id))

    conexao.execute("""
        DELETE FROM chaves
        WHERE id = ?
    """, (chave_id,))

    conexao.commit()
    conexao.close()

    flash("Chave excluída com sucesso.", "sucesso")
    return redirect(url_for("chaves"))



# =========================
# RETIRADA DE CHAVE
# =========================

@app.route("/retirada", methods=["GET", "POST"])
def retirada():
    conexao = conectar_banco()

    # Filtros vindos da URL
    # Exemplos:
    # /retirada
    # /retirada?tipo=laboratorio
    # /retirada?tipo=administrativo
    # /retirada?tipo=sala_aula&andar=1
    # /retirada?tipo=sala_aula&andar=2
    tipo_filtro = request.args.get("tipo", "todos")
    andar_filtro = request.args.get("andar", "")

    if request.method == "POST":
        matricula = request.form.get("matricula", "").strip()
        pin = request.form.get("pin", "").strip()
        chave_id = request.form.get("chave_id", "").strip()
        observacao = request.form.get("observacao", "").strip()
        data_retirada = datetime.now().strftime("%d/%m/%Y %H:%M")

        if not matricula:
            conexao.close()
            flash("Digite a matrícula do usuário.", "erro")
            return redirect(url_for("retirada", tipo=tipo_filtro, andar=andar_filtro))
        
        if not pin:
            conexao.close()
            flash("Digite o PIN do usuário.", "erro")
            return redirect(url_for("retirada", tipo=tipo_filtro, andar=andar_filtro))

        if not pin.isdigit() or len(pin) != 4:
            conexao.close()
            flash("O PIN deve conter exatamente 4 números.", "erro")
            return redirect(url_for("retirada", tipo=tipo_filtro, andar=andar_filtro))

        if not chave_id:
            conexao.close()
            flash("Selecione uma chave antes de registrar a retirada.", "erro")
            return redirect(url_for("retirada", tipo=tipo_filtro, andar=andar_filtro))

        usuario = conexao.execute("""
            SELECT *
            FROM usuarios
            WHERE matricula = ?
        """, (matricula,)).fetchone()

        if not usuario:
            conexao.close()
            flash("Usuário não encontrado. Cadastre o usuário antes da retirada.", "erro")
            return redirect(url_for("cadastrar_usuario"))


        if not usuario["pin_hash"]:
            conexao.close()
            flash("Este usuário ainda não possui PIN cadastrado. Edite o usuário e cadastre um PIN.", "erro")
            return redirect(url_for("retirada", tipo=tipo_filtro, andar=andar_filtro))

        if not check_password_hash(usuario["pin_hash"], pin):
            conexao.close()
            flash("PIN incorreto para a matrícula informada.", "erro")
            return redirect(url_for("retirada", tipo=tipo_filtro, andar=andar_filtro))


        chave = conexao.execute("""
            SELECT *
            FROM chaves
            WHERE id = ?
        """, (chave_id,)).fetchone()

        if not chave:
            conexao.close()
            flash("Chave não encontrada.", "erro")
            return redirect(url_for("retirada", tipo=tipo_filtro, andar=andar_filtro))

        if chave["status"] != "Disponível":
            conexao.close()
            flash("Essa chave não está disponível para retirada.", "erro")
            return redirect(url_for("retirada", tipo=tipo_filtro, andar=andar_filtro))

        conexao.execute("""
            INSERT INTO movimentacoes (
                usuario_id,
                chave_id,
                data_retirada,
                data_devolucao,
                status,
                observacao
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
        return redirect(url_for("retirada", tipo=tipo_filtro, andar=andar_filtro))

    # Parte do GET: monta a consulta das chaves com filtros
    query_chaves = """
        SELECT *
        FROM chaves
        WHERE 1 = 1
    """

    parametros_chaves = []

    if tipo_filtro != "todos":
        query_chaves += " AND tipo = ?"
        parametros_chaves.append(tipo_filtro)

    if andar_filtro:
        query_chaves += " AND andar = ?"
        parametros_chaves.append(andar_filtro)

    query_chaves += """
        ORDER BY
            CASE
                WHEN tipo = 'sala_aula' AND andar = 1 THEN 1
                WHEN tipo = 'sala_aula' AND andar = 2 THEN 2
                WHEN tipo = 'laboratorio' THEN 3
                WHEN tipo = 'administrativo' THEN 4
                ELSE 5
            END,
            local ASC
    """

    chaves = conexao.execute(query_chaves, parametros_chaves).fetchall()

    conexao.close()

    return render_template(
        "retirada.html",
        chaves=chaves,
        tipo_filtro=tipo_filtro,
        andar_filtro=andar_filtro
    )

# =========================
# DEVOLUÇÃO DE CHAVE
# =========================

@app.route("/devolucao", methods=["GET", "POST"])
def devolucao():
    conexao = conectar_banco()

    if request.method == "POST":
        movimentacao_id = request.form.get("movimentacao_id", "").strip()
        matricula_devolucao = request.form.get("matricula_devolucao", "").strip()
        pin = request.form.get("pin", "").strip()
        data_devolucao = datetime.now().strftime("%d/%m/%Y %H:%M")

        if not movimentacao_id:
            conexao.close()
            flash("Movimentação não encontrada.", "erro")
            return redirect(url_for("devolucao"))

        if not matricula_devolucao:
            conexao.close()
            flash("Digite a matrícula de quem está devolvendo a chave.", "erro")
            return redirect(url_for("devolucao"))

        if not pin:
            conexao.close()
            flash("Digite o PIN de quem está devolvendo a chave.", "erro")
            return redirect(url_for("devolucao"))

        if not pin.isdigit() or len(pin) != 4:
            conexao.close()
            flash("O PIN deve conter exatamente 4 números.", "erro")
            return redirect(url_for("devolucao"))

        usuario_devolucao = conexao.execute("""
            SELECT *
            FROM usuarios
            WHERE matricula = ?
        """, (matricula_devolucao,)).fetchone()

        if not usuario_devolucao:
            conexao.close()
            flash("Usuário responsável pela devolução não encontrado.", "erro")
            return redirect(url_for("devolucao"))

        if not usuario_devolucao["pin_hash"]:
            conexao.close()
            flash("Este usuário ainda não possui PIN cadastrado. Edite o usuário e cadastre um PIN.", "erro")
            return redirect(url_for("devolucao"))

        if not check_password_hash(usuario_devolucao["pin_hash"], pin):
            conexao.close()
            flash("PIN incorreto para a matrícula informada.", "erro")
            return redirect(url_for("devolucao"))

        movimentacao = conexao.execute("""
            SELECT *
            FROM movimentacoes
            WHERE id = ?
              AND status = 'Em aberto'
        """, (movimentacao_id,)).fetchone()

        if not movimentacao:
            conexao.close()
            flash("Essa movimentação não está em aberto.", "erro")
            return redirect(url_for("devolucao"))

        conexao.execute("""
            UPDATE movimentacoes
            SET data_devolucao = ?,
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
        return redirect(url_for("devolucao"))

    movimentacoes = conexao.execute("""
        SELECT
            movimentacoes.id,
            movimentacoes.data_retirada,
            movimentacoes.status,

            usuarios.nome AS nome_retirada,
            usuarios.matricula AS matricula_retirada,

            chaves.codigo,
            chaves.local

        FROM movimentacoes

        JOIN usuarios
            ON movimentacoes.usuario_id = usuarios.id

        JOIN chaves
            ON movimentacoes.chave_id = chaves.id

        WHERE movimentacoes.status = 'Em aberto'

        ORDER BY movimentacoes.id DESC
    """).fetchall()

    conexao.close()

    return render_template("devolucao.html", movimentacoes=movimentacoes)


# =========================
# HISTÓRICO
# =========================

@app.route("/historico")
def historico():
    busca = request.args.get("busca", "").strip()
    pessoa = request.args.get("pessoa", "").strip()
    matricula = request.args.get("matricula", "").strip()
    sala = request.args.get("sala", "").strip()
    chave = request.args.get("chave", "").strip()
    status = request.args.get("status", "").strip()
    periodo = request.args.get("periodo", "").strip()
    tipo_data = request.args.get("tipo_data", "retirada").strip()
    data_inicio = request.args.get("data_inicio", "").strip()
    data_fim = request.args.get("data_fim", "").strip()
    hora_inicio = request.args.get("hora_inicio", "").strip()
    hora_fim = request.args.get("hora_fim", "").strip()

    conexao = conectar_banco()

    movimentacoes_brutas = conexao.execute("""
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

        ORDER BY movimentacoes.id DESC
    """).fetchall()

    conexao.close()

    movimentacoes = [dict(mov) for mov in movimentacoes_brutas]

    def texto_contem(valor, filtro):
        return filtro.lower() in str(valor or "").lower()

    def converter_data(valor):
        if not valor:
            return None

        try:
            return datetime.strptime(valor, "%d/%m/%Y %H:%M")
        except ValueError:
            return None

    def converter_data_input(valor):
        if not valor:
            return None

        try:
            return datetime.strptime(valor, "%Y-%m-%d")
        except ValueError:
            return None

    def converter_hora_input(valor):
        if not valor:
            return None

        try:
            return datetime.strptime(valor, "%H:%M").time()
        except ValueError:
            return None

    agora = datetime.now()

    data_inicio_convertida = converter_data_input(data_inicio)
    data_fim_convertida = converter_data_input(data_fim)

    hora_inicio_convertida = converter_hora_input(hora_inicio)
    hora_fim_convertida = converter_hora_input(hora_fim)

    inicio_periodo = None

    if periodo == "hoje":
        inicio_periodo = datetime(agora.year, agora.month, agora.day)

    elif periodo == "semana":
        inicio_periodo = agora - timedelta(days=7)

    elif periodo == "mes":
        inicio_periodo = agora - timedelta(days=30)

    elif periodo == "mes_atual":
        inicio_periodo = datetime(agora.year, agora.month, 1)

    movimentacoes_filtradas = []

    for mov in movimentacoes:
        data_retirada = converter_data(mov["data_retirada"])
        data_devolucao = converter_data(mov["data_devolucao"])

        if tipo_data == "devolucao":
            data_referencia = data_devolucao
        else:
            data_referencia = data_retirada

        if busca:
            campos_busca = [
                mov["nome_retirada"],
                mov["matricula_retirada"],
                mov["nome_devolucao"],
                mov["matricula_devolucao"],
                mov["codigo"],
                mov["local"],
                mov["status"],
                mov["observacao"]
            ]

            if not any(texto_contem(campo, busca) for campo in campos_busca):
                continue

        if pessoa:
            if not (
                texto_contem(mov["nome_retirada"], pessoa)
                or texto_contem(mov["nome_devolucao"], pessoa)
            ):
                continue

        if matricula:
            if not (
                texto_contem(mov["matricula_retirada"], matricula)
                or texto_contem(mov["matricula_devolucao"], matricula)
            ):
                continue

        if sala:
            if not texto_contem(mov["local"], sala):
                continue

        if chave:
            if not texto_contem(mov["codigo"], chave):
                continue

        if status:
            if mov["status"] != status:
                continue

        if periodo:
            if data_referencia is None or data_referencia < inicio_periodo:
                continue

        if data_inicio_convertida:
            if data_referencia is None or data_referencia.date() < data_inicio_convertida.date():
                continue

        if data_fim_convertida:
            if data_referencia is None or data_referencia.date() > data_fim_convertida.date():
                continue

        if hora_inicio_convertida:
            if data_referencia is None or data_referencia.time() < hora_inicio_convertida:
                continue

        if hora_fim_convertida:
            if data_referencia is None or data_referencia.time() > hora_fim_convertida:
                continue

        movimentacoes_filtradas.append(mov)

    return render_template(
        "historico.html",
        movimentacoes=movimentacoes_filtradas,
        busca=busca,
        pessoa=pessoa,
        matricula=matricula,
        sala=sala,
        chave=chave,
        status=status,
        periodo=periodo,
        tipo_data=tipo_data,
        data_inicio=data_inicio,
        data_fim=data_fim,
        hora_inicio=hora_inicio,
        hora_fim=hora_fim
    )

# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    periodo = request.args.get("periodo", "6m")

    dados = obter_dados_dashboard(periodo)

    return render_template("dashboard.html", **dados)



@app.route("/dashboard/pdf")
def exportar_dashboard_pdf():
    periodo = request.args.get("periodo", "6m")
    dados = obter_dados_dashboard(periodo)

    pasta_exports = "exports"

    if not os.path.exists(pasta_exports):
        os.makedirs(pasta_exports)

    caminho_pdf = os.path.join(
        pasta_exports,
        f"dashboard_chaves_{periodo}.pdf"
    )

    documento = SimpleDocTemplate(
        caminho_pdf,
        pagesize=landscape(A4),
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24
    )

    estilos = getSampleStyleSheet()
    elementos = []

    titulo = Paragraph("Dashboard - Sistema de Controle de Chaves", estilos["Title"])
    subtitulo = Paragraph(
        f"Período analisado: {dados['periodo_label']}<br/>"
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        estilos["Normal"]
    )

    elementos.append(titulo)
    elementos.append(subtitulo)
    elementos.append(Spacer(1, 14))

    tabela_kpis = Table([
        ["Indicador", "Valor"],
        ["Total de chaves", dados["total_chaves"]],
        ["Chaves disponíveis", dados["chaves_disponiveis"]],
        ["Chaves retiradas", dados["chaves_retiradas"]],
        ["Movimentos em aberto", dados["movimentos_abertos"]],
        ["Usuários cadastrados", dados["total_usuarios"]],
        ["Movimentações no período", dados["total_movimentacoes"]],
        ["Tempo médio de devolução", dados["tempo_medio_devolucao"]],
        ["Em aberto há mais de 24h", dados["devolucoes_atrasadas"]],
        ["Chave mais utilizada", dados["chave_mais_utilizada"]],
        ["Usuário com mais retiradas", dados["usuario_mais_ativo"]],
    ], colWidths=[220, 300])

    tabela_kpis.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003f91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4ff")]),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(Paragraph("Indicadores gerais", estilos["Heading2"]))
    elementos.append(tabela_kpis)
    elementos.append(Spacer(1, 16))

    top_chaves_pdf = [["Chave / Local", "Usos"]]

    for label, valor in dados["top_chaves"]:
        top_chaves_pdf.append([label, valor])

    if len(top_chaves_pdf) == 1:
        top_chaves_pdf.append(["Nenhum dado no período", "-"])

    tabela_top_chaves = Table(top_chaves_pdf, colWidths=[380, 80])
    tabela_top_chaves.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003f91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4ff")]),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(Paragraph("Top 5 chaves mais utilizadas", estilos["Heading2"]))
    elementos.append(tabela_top_chaves)
    elementos.append(Spacer(1, 16))

    top_usuarios_pdf = [["Usuário", "Retiradas"]]

    for label, valor in dados["top_usuarios"]:
        top_usuarios_pdf.append([label, valor])

    if len(top_usuarios_pdf) == 1:
        top_usuarios_pdf.append(["Nenhum dado no período", "-"])

    tabela_top_usuarios = Table(top_usuarios_pdf, colWidths=[380, 80])
    tabela_top_usuarios.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003f91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4ff")]),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(Paragraph("Top 5 usuários com mais retiradas", estilos["Heading2"]))
    elementos.append(tabela_top_usuarios)
    elementos.append(Spacer(1, 16))

    pendencias_pdf = [["Chave", "Local", "Responsável", "Retirada", "Tempo em aberto"]]

    for item in dados["retiradas_abertas"]:
        pendencias_pdf.append([
            item["codigo"],
            item["local"],
            item["responsavel"],
            item["data_retirada"],
            item["tempo_aberto_formatado"]
        ])

    if len(pendencias_pdf) == 1:
        pendencias_pdf.append(["Nenhuma", "-", "-", "-", "-"])

    tabela_pendencias = Table(
        pendencias_pdf,
        colWidths=[70, 80, 180, 110, 130]
    )

    tabela_pendencias.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003f91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4ff")]),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(Paragraph("Chaves há mais tempo em aberto", estilos["Heading2"]))
    elementos.append(tabela_pendencias)

    documento.build(elementos)

    return send_file(
        caminho_pdf,
        as_attachment=True,
        download_name=f"dashboard_chaves_{periodo}.pdf"
    )



# =========================
# EXPORTAÇÃO CSV
# =========================



def buscar_historico_filtrado(args):
    conexao = conectar_banco()

    busca = args.get("busca", "").strip()
    pessoa = args.get("pessoa", "").strip()
    matricula = args.get("matricula", "").strip()
    sala = args.get("sala", "").strip()
    chave = args.get("chave", "").strip()
    status = args.get("status", "").strip()
    tipo_data = args.get("tipo_data", "retirada").strip()
    periodo = args.get("periodo", "").strip()
    data_inicio = args.get("data_inicio", "").strip()
    data_fim = args.get("data_fim", "").strip()
    hora_inicio = args.get("hora_inicio", "").strip()
    hora_fim = args.get("hora_fim", "").strip()

    coluna_data = "movimentacoes.data_devolucao" if tipo_data == "devolucao" else "movimentacoes.data_retirada"

    data_sql = f"""
        substr({coluna_data}, 7, 4) || '-' ||
        substr({coluna_data}, 4, 2) || '-' ||
        substr({coluna_data}, 1, 2)
    """

    hora_sql = f"substr({coluna_data}, 12, 5)"

    query = """
        SELECT
            movimentacoes.id,
            movimentacoes.data_retirada,
            movimentacoes.data_devolucao,
            movimentacoes.status,
            movimentacoes.observacao,

            usuario_retirada.nome AS nome_retirada,
            usuario_retirada.matricula AS matricula_retirada,
            usuario_retirada.curso_setor AS curso_setor_retirada,

            usuario_devolucao.nome AS nome_devolucao,
            usuario_devolucao.matricula AS matricula_devolucao,

            chaves.codigo,
            chaves.local,
            chaves.descricao

        FROM movimentacoes

        JOIN usuarios AS usuario_retirada
            ON movimentacoes.usuario_id = usuario_retirada.id

        LEFT JOIN usuarios AS usuario_devolucao
            ON movimentacoes.usuario_devolucao_id = usuario_devolucao.id

        JOIN chaves
            ON movimentacoes.chave_id = chaves.id

        WHERE 1 = 1
    """

    parametros = []

    if busca:
        termo = f"%{busca}%"
        query += """
            AND (
                chaves.codigo LIKE ?
                OR chaves.local LIKE ?
                OR chaves.descricao LIKE ?
                OR usuario_retirada.nome LIKE ?
                OR usuario_retirada.matricula LIKE ?
                OR usuario_devolucao.nome LIKE ?
                OR usuario_devolucao.matricula LIKE ?
                OR movimentacoes.status LIKE ?
                OR movimentacoes.observacao LIKE ?
            )
        """
        parametros.extend([termo] * 9)

    if pessoa:
        termo = f"%{pessoa}%"
        query += """
            AND (
                usuario_retirada.nome LIKE ?
                OR usuario_devolucao.nome LIKE ?
            )
        """
        parametros.extend([termo, termo])

    if matricula:
        termo = f"%{matricula}%"
        query += """
            AND (
                usuario_retirada.matricula LIKE ?
                OR usuario_devolucao.matricula LIKE ?
            )
        """
        parametros.extend([termo, termo])

    if sala:
        query += " AND chaves.local LIKE ?"
        parametros.append(f"%{sala}%")

    if chave:
        query += " AND chaves.codigo LIKE ?"
        parametros.append(f"%{chave}%")

    if status and status.lower() not in ["todos", "todo"]:
        status_normalizado = status

        if status.lower() in ["aberto", "em_aberto", "em aberto"]:
            status_normalizado = "Em aberto"
        elif status.lower() in ["finalizado", "finalizada"]:
            status_normalizado = "Finalizada"

        query += " AND movimentacoes.status = ?"
        parametros.append(status_normalizado)

    if periodo and periodo.lower() not in ["todos", "todo"]:
        hoje = datetime.now()

        if periodo in ["1_dia", "1dia", "dia", "hoje"]:
            data_limite = hoje - timedelta(days=1)
        elif periodo in ["7_dias", "7dias", "7"]:
            data_limite = hoje - timedelta(days=7)
        elif periodo in ["1_mes", "1mes", "30_dias", "30dias"]:
            data_limite = hoje - timedelta(days=30)
        elif periodo in ["6_meses", "6meses", "180_dias", "180dias"]:
            data_limite = hoje - timedelta(days=180)
        else:
            data_limite = None

        if data_limite:
            query += f" AND ({data_sql}) >= ?"
            parametros.append(data_limite.strftime("%Y-%m-%d"))

    if data_inicio:
        query += f" AND ({data_sql}) >= ?"
        parametros.append(data_inicio)

    if data_fim:
        query += f" AND ({data_sql}) <= ?"
        parametros.append(data_fim)

    if hora_inicio:
        query += f" AND ({hora_sql}) >= ?"
        parametros.append(hora_inicio)

    if hora_fim:
        query += f" AND ({hora_sql}) <= ?"
        parametros.append(hora_fim)

    query += " ORDER BY movimentacoes.id DESC"

    movimentacoes = conexao.execute(query, parametros).fetchall()
    conexao.close()

    return movimentacoes


@app.route("/exportar-historico")
def exportar_historico():
    movimentacoes = buscar_historico_filtrado(request.args)

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
            "Quem retirou",
            "Matrícula retirada",
            "Curso/Setor",
            "Quem devolveu",
            "Matrícula devolução",
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
                mov["descricao"] or "",
                mov["nome_retirada"],
                mov["matricula_retirada"],
                mov["curso_setor_retirada"] or "",
                mov["nome_devolucao"] or "",
                mov["matricula_devolucao"] or "",
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


@app.route("/exportar-historico-pdf")
def exportar_historico_pdf():
    movimentacoes = buscar_historico_filtrado(request.args)

    pasta_exports = "exports"

    if not os.path.exists(pasta_exports):
        os.makedirs(pasta_exports)

    caminho_pdf = os.path.join(pasta_exports, "historico_chaves.pdf")

    documento = SimpleDocTemplate(
        caminho_pdf,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    estilos = getSampleStyleSheet()
    elementos = []

    titulo = Paragraph("Relatório de Histórico de Chaves", estilos["Title"])
    subtitulo = Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        estilos["Normal"]
    )

    elementos.append(titulo)
    elementos.append(subtitulo)
    elementos.append(Spacer(1, 12))

    dados_tabela = [
        [
            "ID",
            "Chave",
            "Local",
            "Quem retirou",
            "Mat. retirada",
            "Quem devolveu",
            "Mat. devolução",
            "Retirada",
            "Devolução",
            "Status"
        ]
    ]

    for mov in movimentacoes:
        dados_tabela.append([
            mov["id"],
            mov["codigo"],
            mov["local"],
            mov["nome_retirada"],
            mov["matricula_retirada"],
            mov["nome_devolucao"] or "-",
            mov["matricula_devolucao"] or "-",
            mov["data_retirada"],
            mov["data_devolucao"] or "-",
            mov["status"]
        ])

    if len(dados_tabela) == 1:
        elementos.append(Paragraph("Nenhuma movimentação encontrada para os filtros aplicados.", estilos["Normal"]))
    else:
        tabela = Table(
            dados_tabela,
            repeatRows=1,
            colWidths=[30, 55, 75, 100, 75, 100, 75, 80, 80, 65]
        )

        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d47a1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6fc")])
        ]))

        elementos.append(tabela)

    documento.build(elementos)

    return send_file(
        caminho_pdf,
        as_attachment=True,
        download_name="historico_chaves.pdf"
    )



# =========================
# INICIAR SISTEMA
# =========================

if __name__ == "__main__":
    criar_tabelas()
    app.run(host="192.168.0.101", port=5000, debug=True)
    
