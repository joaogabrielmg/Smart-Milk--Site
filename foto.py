import mysql.connector

# Conectar ao banco
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root',
    database='mimosa'
)
cursor = conn.cursor()

# Nome do usuário e caminho da imagem
nome_usuario = 'Barbara'
caminho_imagem = 'face/barbara.png'

# Lê a imagem como bytes
with open(caminho_imagem, 'rb') as f:
    imagem_bytes = f.read()

# Atualiza a imagem do usuário específico
sql = "UPDATE usuario SET foto = %s WHERE nome = %s"
valores = (imagem_bytes, nome_usuario)
cursor.execute(sql, valores)
conn.commit()

print(f"Imagem de {nome_usuario} atualizada com sucesso!")
cursor.close()
conn.close()
