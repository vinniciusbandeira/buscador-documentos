import streamlit as st
import sqlite3
import bcrypt
import os
from sqlalchemy import create_engine, text

# =========================
# CONFIGURAÇÃO DO BANCO
# =========================
DB_PATH = "documentos.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

# =========================
# FUNÇÃO DE LOGIN
# =========================
def verificar_login(username, senha):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT senha_hash FROM usuarios WHERE username = ?", (username,))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        return bcrypt.checkpw(senha.encode(), resultado[0])
    return False


# =========================
# CONTROLE DE SESSÃO
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
            st.error("Usuário ou senha incorretos.")

    st.stop()  # 🚨 impede o resto do app de rodar


# =========================
# SISTEMA PRINCIPAL (SÓ APÓS LOGIN)
# =========================

st.title("📂 Buscador de Documentos")

palavra = st.text_input("Digite a palavra para buscar:")

if palavra:
    with engine.connect() as conn:
        resultados = conn.execute(text("""
            SELECT nome, caminho
            FROM documentos_fts
            WHERE conteudo LIKE :palavra
        """), {"palavra": f"%{palavra}%"}).fetchall()

        if resultados:
            st.write("Resultados encontrados:")

            for nome, caminho in resultados:
                st.markdown(f"### 📄 {nome}")

                try:
                    with open(caminho, "rb") as f:
                        st.download_button(
                            label="⬇ Baixar arquivo",
                            data=f,
                            file_name=nome,
                            key=caminho
                        )
                except:
                    st.warning("Arquivo não encontrado.")

        else:
            st.write("Nenhum documento encontrado.")


# =========================
# BOTÃO DE LOGOUT
# =========================
if st.button("🚪 Sair"):
    st.session_state.logado = False
    st.rerun()