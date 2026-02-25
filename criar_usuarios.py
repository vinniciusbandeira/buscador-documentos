import sqlite3
import bcrypt

conn = sqlite3.connect("documentos.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    senha_hash TEXT
)
""")

def criar_usuario(username, senha):
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
    cursor.execute(
        "INSERT INTO usuarios (username, senha_hash) VALUES (?, ?)",
        (username, senha_hash)
    )
    conn.commit()

# 👇 CRIE SEU PRIMEIRO USUÁRIO AQUI
criar_usuario("admin", "123456")

print("Usuário criado com sucesso!")

conn.close()
