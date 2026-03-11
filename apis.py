from flask import Flask, abort, request, jsonify
from flask_cors import CORS
from flask import send_file
import datetime
import mysql.connector
import io
from mysql.connector import Error
from flask import send_file,jsonify

app = Flask(__name__)
CORS(app)  # Permite o acesso entre origens diferentes (CORS)

# Configuração do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'mimosa'
}
#---------------------------------------------------------------
@app.route('/usuario', methods=['GET'])#forma uma requisição para o servidor,de acordo com a pagina
def get_usuario():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()#Configuração do banco 
        cursor.execute("SELECT nome FROM usuario WHERE cargo = 0")#comando para pegar dados do mysql(produtor)
        rows = cursor.fetchall()

        nomes = [row[0] for row in rows] #pega somente os nomes
        return jsonify(nomes)#para ser demonstrado 

    except mysql.connector.Error as err:
        return jsonify({"erro": str(err)}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

#----------------------------------------
@app.route('/login', methods=['POST']) #comando do login,(Publica)
def login():
    usuario = request.form.get('usuario')#pega os dados escritos no login
    senha = request.form.get('senha')
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM usuario WHERE nome = %s AND senha = %s", (usuario, senha))#procura para existir
        user = cursor.fetchone()

        if user:#verifica se cargo é de admin
            if user['cargo'] == 1:
                return jsonify({'status': 'ok', 'message': 'Login bem-sucedido!'})
            else:
                return jsonify({'status': 'error', 'message': 'Acesso negado, cargo insuficiente.'})
        else:
            return jsonify({'status': 'error', 'message': 'Usuário ou senha inválidos.'})

    except mysql.connector.Error as err:
        return jsonify({'status': 'error', 'message': f'Erro ao acessar o banco de dados: {err}'})

    finally:#fecha a conexão 
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
#-----------------------------------------------
@app.route('/detalhespro', methods=['GET'])
def detalhes_produtor():
    nome = request.args.get('nome')
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT nome, idtanque, idregiao, saldo, litros
            FROM usuario
            WHERE nome = %s
        """, (nome,))#imprime uma tela com todos os dados dos produtores da tabela
        row = cursor.fetchone()
        if row:
            return jsonify(row)
        else:
            return jsonify({'erro': 'Produtor não encontrado'}), 404
    except mysql.connector.Error as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

#------------------------------------------------------------------
@app.route('/tanque', methods=['GET'])#pega os tanques disponiveis 
def tanque(): 
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT idtanque, idregiao FROM tanque") #demonstra os ids do tanque
        dados = cursor.fetchall()
        return jsonify(dados)
    except Error as err:
        return jsonify({'status': 'error', 'message': f'Erro ao acessar os tanques: {err}'})
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
#----------------------------------------------------------------------
@app.route('/tanque/<int:idtanque>/<int:idregiao>', methods=['GET'])#deixa salvo o id do tanque
def dados_tanque(idtanque, idregiao):
    try:
        resultado = buscar_dados_do_tanque(idtanque, idregiao)
        return jsonify(resultado)
    except Error as err:
        return jsonify({'status': 'error', 'message': f'Erro ao buscar dados do tanque: {err}'})

# --------------------------------------------------------------------
def buscar_dados_do_tanque(idtanque, idregiao): #demonstra os dados do tanque de acordo com o id salvo
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT  ph,temp,nivel,amonia,carbono,metano
            FROM tanque
            WHERE idtanque = %s AND idregiao = %s
        """
        cursor.execute(query, (idtanque, idregiao))
        resultado = cursor.fetchone()
        return resultado if resultado else {'message': 'Tanque não encontrado'}
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
#---------------------------------------------------------------------------
@app.route('/historico_temperatura/<int:idtanque>/<int:idregiao>', methods=['GET'])
def historico_temperatura(idtanque, idregiao):#historico da temperatura do tanque,pelo id selecionado 
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        query = "SELECT temp,datahora FROM temp WHERE idtanque = %s AND idregiao = %s" #seleciona os dados da temp
        cursor.execute(query, (idtanque, idregiao))
        resultados = cursor.fetchall()
        return jsonify(resultados)
    except mysql.connector.Error as err:
        return jsonify({'status': 'error', 'message': f'Erro ao acessar o banco de dados: {err}'})
    finally:#fecha a conexão
        if connection.is_connected():
            cursor.close()
            connection.close()
#-----------------Cadastro-------------------------------        
@app.route('/cadastro', methods=['POST'])#publica os dados no forme
def cadastro():
    usuario = request.form.get('usuario')
    senha = request.form.get('senha')#cadastro no site 
    confirmar = request.form.get('confirmar')
    cargo_str = request.form.get('setor')

    try:
        idtanque = int(request.form.get('idtanque'))
        idregiao = int(request.form.get('idregiao'))#se seleciona os ids para essa ação 
    except (TypeError, ValueError):
        return "Erro: Tanque e Região devem ser números válidos."

    if senha != confirmar:
        return "As senhas não coincidem."

    if cargo_str.lower() == 'produtor':
        cargo = 0
    elif cargo_str.lower() == 'administrador':
        cargo = 1
    elif cargo_str.lower() == 'coletor':
        cargo = 2
    else:
        return "Cargo inválido. Use: produtor, coletor ou administrador."

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        print(f"Enviando para o banco: usuario={usuario}, senha={senha}, idtanque={idtanque}, idregiao={idregiao}, cargo={cargo}")

        query = "INSERT INTO usuario (nome, senha, idtanque, idregiao, cargo) VALUES (%s, %s, %s, %s, %s)"#Salva os valores no banco de dados
        valores = (usuario, senha, idtanque, idregiao, cargo)
        cursor.execute(query, valores)
        connection.commit()
        return "Usuário cadastrado com sucesso!"

    except mysql.connector.Error as err:
        return f"Erro no banco de dados: {err}"

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
#----------------------imagem------------------------------------
@app.route('/imagem', methods=['GET'])#pega a imagem salva de acordo com os nomes das pessoas na tabela de produtor 
def retornar_imagem():
    nome = request.args.get('nome')
    print(f"Requisitando imagem para nome: {nome}")

    if not nome:
        return abort(400, "Nome não fornecido")

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT foto FROM usuario WHERE nome = %s", (nome,))#pega a foto e a imagem do produtor
        resultado = cursor.fetchone()
        cursor.close()
        connection.close()

        if resultado and resultado[0]:
            return send_file(io.BytesIO(resultado[0]), mimetype='image/jpeg')
        else:
            return abort(404, "Imagem não encontrada")
    except mysql.connector.Error as err:
        return jsonify({'status': 'error', 'message': f'Erro no banco de dados: {err}'}), 500
    
#----------------------carros-----------------------------
@app.route('/caminhao')
def pagina_caminhao():
    # Serve o arquivo HTML puro, sem tentar renderizar template
    return send_file("caminhao.html", mimetype='text/html')

@app.route('/api/carros')
def api_carros():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT placa, coletor FROM coletores")#demonstra os carros disponiveis e cada coletor
        carros = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(carros)
    except mysql.connector.Error as err:
        return jsonify({'status': 'error', 'message': f'Erro ao acessar banco de dados: {err}'}), 500
#------------------------solicitações------------------------------------
@app.route('/solicitacao',methods=['GET'])#pega os dados que estão vazio 
def solicitacao():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT nome FROM usuario WHERE cargo IS NULL")
        rows = cursor.fetchall()#pega todas as coisas do banco
        nome = [row[0] for row in rows]#pega os nomes para ser demonstrados no formato 
        return jsonify(nome)#retorna o nome estilo vetor
    except mysql.connector.Error as err:
        return jsonify ({"erro": str(err)}),500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
#-----------------------------formulario--------------------------------------       
@app.route('/atualizar_user', methods=['POST'])#forma uma requisição para o servidor 
def atualizar_user():
    dados = request.get_json()
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        for item in dados:
            nome = item['nome']
            cargo_str = item['cargo']

            if cargo_str == "excluir":
                cursor.execute("DELETE FROM usuario WHERE nome = %s", (nome,))#excluir o user(recusado)
            elif cargo_str == "0":
                cursor.execute("UPDATE usuario SET cargo = 0 WHERE nome = %s", (nome,))
            elif cargo_str == "2":
                cursor.execute("UPDATE usuario SET cargo = 2 WHERE nome = %s", (nome,))
                
        connection.commit()
        return jsonify({'status': 'ok', 'message': 'Alterações salvas com sucesso!'})

    except mysql.connector.Error as err:
        return jsonify({'status': 'erro', 'message': str(err)}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
# ------------------------- Histórico por data ----------------------------
@app.route('/api/historico', methods=['GET'])
def historico_por_data():
    data_str = request.args.get('data')  # Formato esperado: 'YYYY-MM-DD'

    if not data_str:
        return jsonify({'erro': 'Parâmetro "data" não fornecido.'}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT idtanque, idregiao, datahora
            FROM historico
            WHERE DATE(datahora) = %s
            ORDER BY datahora ASC
        """
        cursor.execute(query, (data_str,))
        resultados = cursor.fetchall()

        # Força o campo datahora a ser convertido para string no formato ISO
        for row in resultados:
            if isinstance(row['datahora'], (datetime.datetime, datetime.date)):
                row['datahora'] = row['datahora'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(resultados)

    except mysql.connector.Error as err:
        return jsonify({'erro': f'Erro ao acessar o banco de dados: {err}'}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

#=---------------------------------Cad coletores/Caminhão-----------------------------------------------------------

@app.route('/cadastrar_placa', methods=['POST'])
def cadastrar_placa():
    nome = request.form.get('nome')
    placa = request.form.get('placa')
    if not nome or not placa:
        return jsonify({"status": "erro", "message": "Preencha todos os campos."})

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(buffered=True)

        cursor.execute("SELECT * FROM coletores WHERE coletor = %s", (nome,))
        resultado = cursor.fetchone()

        if resultado:
            cursor.execute("UPDATE coletores SET placa = %s WHERE coletor = %s", (placa, nome))
            connection.commit()
            return jsonify({"status": "ok", "message": "Cadastrado com sucesso!"})
        else:
            return jsonify({"status": "erro", "message": "Não foi possível cadastrar. Coletor não encontrado."})

    except mysql.connector.Error as err:
        return jsonify({"status": "erro", "message": f"Erro no banco de dados: {err}"})

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


#-----------------------------------Gerenciamento de Vacas------------------------------------------------------------
@app.route('/vacas', methods=['GET'])
def listar_vacas_por_usuario():
    nome_usuario = request.args.get('nome')
    
    if not nome_usuario:
        return jsonify({"erro": "Nome do usuário não foi fornecido na URL."}), 400

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # Primeiro, obter o ID do usuário com base no nome
        cursor.execute("SELECT id FROM usuario WHERE nome = %s", (nome_usuario,))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        id_usuario = usuario['id']

        # Agora buscar as vacas relacionadas a esse usuário
        cursor.execute("""
            SELECT nome, brinco, crias, origem, estado
            FROM vacas
            WHERE usuario_id = %s
        """, (id_usuario,))

        vacas = cursor.fetchall()

        return jsonify(vacas)

    except mysql.connector.Error as err:
        return jsonify({"erro": f"Erro no banco de dados: {err}"}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

#---------------------------upload De Fotos----------------------
@app.route('/upload_imagem', methods=['POST'])
def upload_imagem():
    idtanque = request.form.get('idtanque')
    idregiao = request.form.get('idregiao')
    arquivo = request.files.get('imagem')

    if not idtanque or not idregiao or not arquivo:
        return jsonify({"erro": "Parâmetros faltando. Envie idtanque, idregiao e imagem."}), 400

    try:
        idtanque = int(idtanque)
        idregiao = int(idregiao)
        imagem_bytes = arquivo.read()

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "UPDATE id SET publicacao = %s WHERE idtanque = %s AND idregiao = %s"
        cursor.execute(query, (imagem_bytes, idtanque, idregiao))
        connection.commit()

        print(f"[DEBUG] UPDATE executado. Linhas afetadas: {cursor.rowcount}")
        print(f"[DEBUG] idtanque={idtanque}, idregiao={idregiao}, bytes={len(imagem_bytes)}")

        if cursor.rowcount == 0:
            return jsonify({"erro": "Nenhuma linha atualizada. Verifique se idtanque/idregiao existem."}), 404

        return jsonify({"status": "ok", "mensagem": "Imagem salva com sucesso!"})

    except mysql.connector.Error as err:
        return jsonify({"erro": f"Erro no banco de dados: {err}"}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

#--------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
