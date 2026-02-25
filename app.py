import streamlit as st
import sqlite3
import bcrypt

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Buscador de Documentos", layout="wide")

# =========================
# INICIALIZAÇÃO DO BANCO
# =========================
def inicializar_banco():
    conn = sqlite3.connect("documentos.db")
    cursor = conn.cursor()

    # Criar tabela usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        senha_hash TEXT
    )
    """)

    # Criar tabela documentos (FTS5)
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS documentos_fts
    USING fts5(nome, conteudo)
    """)

    # Criar admin se não existir
    cursor.execute("SELECT * FROM usuarios WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        senha_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO usuarios (username, senha_hash) VALUES (?, ?)",
            ("admin", senha_hash),
        )

    conn.commit()
    conn.close()


inicializar_banco()

# =========================
# FUNÇÕES
# =========================
def verificar_login(username, senha):
    conn = sqlite3.connect("documentos.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT senha_hash FROM usuarios WHERE username = ?", (username,)
    )
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        return bcrypt.checkpw(senha.encode(), resultado[0].encode())

    return False


# =========================
# LOGIN
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
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

else:
    # =========================
    # SISTEMA PRINCIPAL
    # =========================
    st.title("📂 Buscador de Documentos")

    busca = st.text_input("Digite o termo para busca")

    if busca:
        conn = sqlite3.connect("documentos.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT nome FROM documentos_fts WHERE documentos_fts MATCH ?",
            (busca,),
        )

        resultados = cursor.fetchall()
        conn.close()

        if resultados:
            st.subheader("Resultados encontrados:")
            for doc in resultados:
                st.write("📄", doc[0])
        else:
            st.warning("Nenhum resultado encontrado.")

    if st.button("Logout"):
        st.session_state.logado = False
        st.rerun()
