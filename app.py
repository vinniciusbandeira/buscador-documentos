import streamlit as st
import os
import bcrypt
from sqlalchemy import create_engine, text
from pypdf import PdfReader
from docx import Document
import openpyxl

st.set_page_config(page_title="Buscador de Documentos", layout="wide")

# =========================
# CONEXÃO POSTGRESQL
# =========================
DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# =========================
# INICIALIZA BANCO
# =========================
def inicializar_banco():
    with engine.begin() as conn:

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS documentos (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            conteudo TEXT,
            arquivo BYTEA
        );
        """))

        # cria usuário admin se não existir
        result = conn.execute(text(
            "SELECT * FROM usuarios WHERE username = 'admin';"
        ))

        if result.fetchone() is None:
            senha_hash = bcrypt.hashpw(
                "admin123".encode(),
                bcrypt.gensalt()
            ).decode()

            conn.execute(text("""
                INSERT INTO usuarios (username, senha_hash)
                VALUES (:username, :senha_hash);
            """), {"username": "admin", "senha_hash": senha_hash})


inicializar_banco()

# =========================
# LOGIN
# =========================
def verificar_login(username, senha):
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT senha_hash FROM usuarios WHERE username = :u"),
            {"u": username}
        ).fetchone()

    if result:
        return bcrypt.checkpw(senha.encode(), result[0].encode())
    return False


# =========================
# EXTRAIR TEXTO
# =========================
def extrair_texto(arquivo):
    nome = arquivo.name
    extensao = nome.split(".")[-1].lower()

    if extensao == "pdf":
        reader = PdfReader(arquivo)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() or ""
        return texto

    elif extensao == "docx":
        doc = Document(arquivo)
        return "\n".join([p.text for p in doc.paragraphs])

    elif extensao == "xlsx":
        wb = openpyxl.load_workbook(arquivo)
        texto = ""
        for sheet in wb:
            for row in sheet.iter_rows(values_only=True):
                texto += " ".join(
                    [str(cell) for cell in row if cell]
                ) + "\n"
        return texto

    elif extensao == "txt":
        return arquivo.read().decode("utf-8")

    return ""


# =========================
# SALVAR DOCUMENTO
# =========================
def salvar_documento(nome, conteudo, arquivo_bytes):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO documentos (nome, conteudo, arquivo)
            VALUES (:nome, :conteudo, :arquivo)
        """), {
            "nome": nome,
            "conteudo": conteudo,
            "arquivo": arquivo_bytes
        })


# =========================
# INTERFACE
# =========================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🔐 Login")

    username = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if verificar_login(username, senha):
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

else:
    st.title("📂 Buscador de Documentos")

    # UPLOAD
    st.subheader("📤 Upload de Documento")

    arquivo = st.file_uploader(
        "Envie um arquivo",
        type=["pdf", "docx", "xlsx", "txt"]
    )

    if arquivo:
        with st.spinner("Processando..."):
            texto = extrair_texto(arquivo)

            if texto.strip():
                salvar_documento(
                    arquivo.name,
                    texto,
                    arquivo.getvalue()
                )
                st.success("Documento salvo com sucesso!")
            else:
                st.warning("Não foi possível extrair texto.")

    # BUSCA
    st.subheader("🔎 Buscar Documento")

    busca = st.text_input("Digite o termo")

    if busca:
        with engine.begin() as conn:
            resultados = conn.execute(text("""
                SELECT id, nome, arquivo
                FROM documentos
                WHERE conteudo ILIKE :busca
            """), {"busca": f"%{busca}%"}).fetchall()

    if resultados:
            for i, (doc_id, nome, arquivo_blob) in enumerate(resultados):

    # Converte memoryview para bytes
    arquivo_bytes = bytes(arquivo_blob)

    st.write("📄", nome)

    st.download_button(
        label="⬇️ Baixar",
        data=arquivo_bytes,
        file_name=nome,
        key=f"download_{doc_id}_{i}"
    )
        else:
            st.warning("Nenhum resultado encontrado.")

    if st.button("Logout"):
        st.session_state.logado = False
        st.rerun()


