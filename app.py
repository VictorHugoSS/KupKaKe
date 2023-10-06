from flask import Flask, render_template, request, session, redirect, url_for, flash, g, jsonify
import sqlite3

from flask_mail import Mail

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Substitua 'sua_chave_secreta' por uma chave segura

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'  # Substitua pelo seu e-mail
app.config['MAIL_PASSWORD'] = 'sua_senha'  # Substitua pela sua senha
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'victorhugodesouzasilva280@gmail.com'  # Substitua pelo seu e-mail

mail = Mail(app)


# Função para conectar ao banco de dados
def connect_db():
    return sqlite3.connect('app.db')


# Rota para criar o banco de dados (somente uma vez)
@app.route('/create_db')
def create_db():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            senha TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cupcakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco DECIMAL(10, 2) NOT NULL,
            disponivel BOOLEAN DEFAULT 1,
            imagem_url TEXT,
            data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            cupcake_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
            FOREIGN KEY (cupcake_id) REFERENCES cupcakes (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cupcake_id INTEGER NOT NULL,
            pedido_id INTEGER NOT NULL,
            classificacao INTEGER NOT NULL,
            comentario TEXT,
            FOREIGN KEY (cupcake_id) REFERENCES cupcakes (id),
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id)
        )
    ''')

    conn.commit()
    conn.close()

    flash('Banco de dados criado com sucesso', 'success')
    return redirect(url_for('login'))

    flash('Banco de dados criado com sucesso', 'success')
    return redirect(url_for('login'))


DATABASE = 'app.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


# Rota para o formulário de login
from flask import request, session


# ...

def get_cupcakes_from_database():
    cupcakes = []

    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM cupcakes')
        cupcakes_data = cursor.fetchall()

        for cupcake_data in cupcakes_data:
            cupcake = {
                'id': cupcake_data[0],
                'nome': cupcake_data[1],
                'descricao': cupcake_data[2],
                'preco': cupcake_data[3],
                'disponivel': cupcake_data[4],
                'imagem_url': cupcake_data[5],
                'data_adicao': cupcake_data[6]
            }
            cupcakes.append(cupcake)

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print('Erro ao buscar cupcakes do banco de dados:', str(e))

    return cupcakes


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM usuarios WHERE email = ? AND senha = ?', (email, senha))
        usuario = cursor.fetchone()

        conn.commit()
        conn.close()

        if usuario:
            session['usuario_id'] = usuario[0]
            # Verifique se o usuário é um administrador
            print("Valor do campo de administrador:", usuario[5])

            if usuario[
                5] == 1:  # Suponha que o campo que indica se é administrador seja o quarto campo na tabela (índice 3)
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Falha ao tentar logar.', 'error')

    return render_template('login.html')


# Rota para o dashboard (requer login)
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' in session:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],))
        usuario = cursor.fetchone()

        # Buscar os cupcakes do banco de dados (ou de outra fonte)
        cupcakes = get_cupcakes_from_database()

        conn.commit()
        conn.close()

        if usuario:
            return render_template('dashboard.html', usuario=usuario, cupcakes=cupcakes)

    flash('Faça o login para acessar o dashboard', 'error')
    return redirect(url_for('login'))


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'usuario_id' in session:
        conn = connect_db()
        cursor = conn.cursor()
        print("Entrei po")
        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],))
        usuario = cursor.fetchone()

        conn.commit()
        conn.close()
        print("cacete")
        if usuario:
            # Verificar se o usuário é um administrador
            if usuario[5] == 1:  # Suponha que o campo que indica se é administrador seja o quarto campo na tabela (índice 3)
                # Lógica para a página de administração aqui
                print("La vamos nos")
                return render_template('admin_dashboard.html')
            else:
                flash('Você não tem permissão para acessar a página de administração', 'error')
                print("Entrei pombas")
                return redirect(
                    url_for('dashboard'))  # Redireciona para o painel normal se o usuário não for administrador
        else:
            flash('Faça o login para acessar a página de administração', 'error')
            print("CAraho")
            return redirect(url_for('login'))

    flash('Faça o login para acessar a página de administração', 'error')
    return redirect(url_for('login'))


# Rota para logout
@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('login'))


# Rota para o formulário de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        telefone = request.form['telefone']

        conn = connect_db()
        cursor = conn.cursor()

        # Verifique se o email já está em uso
        cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Este email já está associado a uma conta existente. Por favor, faça login ou use outro email.',
                  'error')
        else:
            cursor.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha))
            conn.commit()
            conn.close()
            flash('Usuário registrado com sucesso', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


# Função para obter informações do cupcake com base no ID no banco de dados
def obter_cupcake(cupcake_id):
    try:
        # Conectar ao banco de dados SQLite (substitua 'nome_do_banco.db' pelo nome do seu banco de dados)
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        # Executar uma consulta SQL para buscar o cupcake com base no ID
        cursor.execute('SELECT * FROM cupcakes WHERE id = ?', (cupcake_id,))
        cupcake_data = cursor.fetchone()

        if cupcake_data:
            cupcake_info = {
                'id': cupcake_data[0],
                'nome': cupcake_data[1],
                'descricao': cupcake_data[2],
                'preco': float(cupcake_data[3].replace(',', '.')),  # Substituir ',' por '.'
                'disponivel': bool(cupcake_data[4]),
                'imagem_url': cupcake_data[5]
            }

            # if cupcake_info:
            # print("Informações do Cupcake:")
            # print(cupcake_info)
            # else:
            # print("Cupcake não encontrado.")
            return cupcake_info

    except sqlite3.Error as e:
        # Tratar exceções de banco de dados, se necessário
        print("Erro ao buscar o cupcake:", e)
    finally:
        # Fechar a conexão com o banco de dados
        conn.commit()
        conn.close()

    return None  # Retornar None se o cupcake não for encontrado


@app.route('/limpar-carrinho', methods=['POST'])
def limpar_carrinho():
    session.pop('carrinho', None)  # Remove a variável de sessão 'carrinho'
    flash('Carrinho esvaziado.', 'success')
    return redirect('/carrinho')  # Redireciona de volta para a página do carrinho


@app.route('/adicionar_ao_carrinho', methods=['POST'])
def adicionar_ao_carrinho():
    try:
        # Verifica se 'carrinho' já está na sessão, senão, cria uma lista vazia.
        if 'carrinho' not in session:
            session['carrinho'] = []

        # Obtém os dados do formulário.
        cupcake_id = request.form.get('cupcake_id')
        quantidade = request.form.get('quantidade', type=int)

        # Você deve buscar as informações do cupcake com base no cupcake_id no seu banco de dados.
        # Suponha que você tenha uma função chamada obter_informacoes_do_cupcake.
        cupcake_info = obter_cupcake(cupcake_id)

        if cupcake_info:
            # Verifique se já existe um item com o mesmo cupcake_id no carrinho
            for item in session['carrinho']:
                if item['cupcake']['id'] == cupcake_info['id']:
                    # Se já existe, atualize apenas a quantidade
                    item['quantidade'] += quantidade
                    flash('Quantidade atualizada no carrinho', 'success')
                    break
            else:
                # Se não existe, adicione um novo item ao carrinho
                item = {
                    'cupcake': {
                        'id': cupcake_info['id'],
                        'nome': cupcake_info['nome'],
                        'descricao': cupcake_info['descricao'],
                        'preco': cupcake_info['preco'],
                        'imagem_url': cupcake_info['imagem_url']
                    },
                    'quantidade': quantidade
                }
                session['carrinho'].append(item)
                if quantidade > 1:
                    flash('Cupcakes adicionados ao carrinho', 'success')
                else:
                    flash('Cupcake adicionado ao carrinho', 'success')
        else:
            flash('Cupcake não encontrado.', 'error')

        return redirect(url_for('carrinho'))
    except Exception as e:
        # Lidar com exceções aqui, se necessário
        return str(e), 500  # Retorna uma resposta de erro 500 com a descrição do erro como texto


@app.route('/remover-do-carrinho/<cupcake_id>', methods=['POST'])
def remover_do_carrinho(cupcake_id):
    cupcake_int = int(cupcake_id)
    try:
        print("ENTREI pombas")
        if 'carrinho' in session:
            print("ENTREI maland")
            carrinho = session['carrinho']
            # Verifique se já existe um item com o mesmo cupcake_id no carrinho
            for item in carrinho:
                print("item:")
                print(type(item['cupcake']['id']))
                print(type(cupcake_id))
                if item['cupcake']['id'] == cupcake_int:
                    print(item)
                    print("Falaaa")
                    # Verifique a quantidade
                    if item['quantidade'] > 1:
                        item['quantidade'] -= 1
                    else:
                        # Se a quantidade for 1, remova o item do carrinho
                        carrinho.remove(item)
                    flash('Cupcake removido do carrinho', 'success')
                    break

            # Atualize a sessão com o novo carrinho
            session['carrinho'] = carrinho
        else:
            flash('Carrinho não encontrado na sessão', 'error')

        return redirect(url_for('carrinho'))
    except Exception as e:
        # Lidar com exceções aqui, se necessário
        return str(e), 500  # Retorna uma resposta de erro 500 com a descrição do erro como texto


@app.route('/carrinho', methods=['GET'])
def carrinho():
    if 'carrinho' not in session:
        session['carrinho'] = []

    # Atualize o preço total para cada item no carrinho
    for item in session['carrinho']:
        item['total'] = item['quantidade'] * item['cupcake']['preco']

    return render_template('carrinho.html')


# Rota para a página inicial
@app.route('/')
def home():
    return render_template('login.html')


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'usuario_id' in session:
        if request.method == 'POST':
            nome = request.form['nome']
            email = request.form['email']
            telefone = request.form['telefone']
            senha = request.form['senha']

            conn = connect_db()
            cursor = conn.cursor()

            # Atualizar as informações do perfil no banco de dados
            cursor.execute('UPDATE usuarios SET nome=?, email=?, telefone=?, senha=? WHERE id=?',
                           (nome, email, telefone, senha, session['usuario_id']))
            conn.commit()
            conn.close()

            flash('Perfil atualizado com sucesso', 'success')
            return redirect(url_for('dashboard'))

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],))
        usuario = cursor.fetchone()

        conn.commit()
        conn.close()

        if usuario:
            return render_template('edit_profile.html', usuario=usuario)

    flash('Faça o login para acessar o perfil', 'error')
    return redirect(url_for('login'))


# Rota para gerar relatório de pedidos para atendentes
@app.route('/generate_report')
def generate_report():
    if 'usuario_id' in session:
        if session['tipo_usuario'] == 'atendente':
            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM pedidos')
            pedidos = cursor.fetchall()

            conn.commit()
            conn.close()

            # Você pode implementar a geração do relatório em formato CSV ou PDF aqui

            return render_template('generate_report.html', pedidos=pedidos)

    flash('Faça o login como atendente para gerar relatórios', 'error')
    return redirect(url_for('login'))


@app.route('/admin/add_product', methods=['GET', 'POST'])
def admin_add_product():
    if request.method == 'POST':
        print("Entrei bosta")
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = request.form['preco']
        disponivel = request.form.get('disponivel', False)
        imagem_url = request.form['imagem_url']

        print("Entrei pora")
        conn = connect_db()
        cursor = conn.cursor()

        # Usar uma transação para garantir atomicidade das operações de banco de dados
        conn.execute('BEGIN')

        cursor.execute('''
        INSERT INTO cupcakes (nome, descricao, preco, disponivel, imagem_url)
        VALUES (?, ?, ?, ?, ?)
        ''', (nome, descricao, preco, disponivel, imagem_url))

        conn.commit()
        conn.close()

        flash('Produto adicionado com sucesso', 'success')

        print("Entrei passou")
        return redirect(url_for('admin_dashboard'))

    print("Entrei biruta")
    return render_template('admin_add_product.html')


@app.route('/finalizar_pedido', methods=['POST'])
def finalizar_pedido():
    if 'carrinho' in session:
        carrinho = session['carrinho']
        usuario_id = session.get('usuario_id')

        conn = connect_db()
        cursor = conn.cursor()

        # Crie um registro de pedido no banco de dados
        cursor.execute('INSERT INTO pedidos (usuario_id, status) VALUES (?, ?)', (usuario_id, 'Concluído'))
        pedido_id = cursor.lastrowid

        for item in carrinho:
            cupcake_id = item['cupcake']['id']
            quantidade = item['quantidade']

            # Crie um registro de item de pedido no banco de dados
            cursor.execute('INSERT INTO itens_pedido (pedido_id, cupcake_id, quantidade) VALUES (?, ?, ?)',
                           (pedido_id, cupcake_id, quantidade))

        conn.commit()
        conn.close()

        session.pop('carrinho', None)  # Limpe o carrinho após a conclusão do pedido
        flash('Pedido realizado com sucesso', 'success')

    return redirect(url_for('carrinho'))


@app.route('/avaliar_pedido/<int:pedido_id>', methods=['GET', 'POST'])
def avaliar_pedido(pedido_id):
    # Verifique se o usuário está autenticado
    if 'usuario_id' not in session:
        flash('Faça o login para avaliar o pedido.', 'error')
        return redirect(url_for('login'))

    # Recupere informações do pedido


def obter_item_pedido_por_ids(pedido_id):
    item_pedido = None

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Consulta SQL para buscar o item do pedido com base nos IDs do pedido e do cupcake
        cursor.execute('SELECT * FROM itens_pedido WHERE pedido_id = ? AND cupcake_id = ?', (pedido_id,))
        item_pedido_data = cursor.fetchone()

        if item_pedido_data:
            item_pedido = {
                'id': item_pedido_data[0],
                'pedido_id': item_pedido_data[1],
                'cupcake_id': item_pedido_data[2],
                'quantidade': item_pedido_data[3],
                # Adicione outros campos do item do pedido conforme necessário
            }
            print(item_pedido)

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print('Erro ao buscar item do pedido do banco de dados:', str(e))

    return item_pedido


def salvar_avaliacao_item_pedido(pedido_id, usuario_id, classificacao, comentario):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Verifique se já existe uma avaliação para o item do pedido
        cursor.execute('SELECT * FROM avaliacoes WHERE pedido_id = ? AND usuario_id = ?', (pedido_id, usuario_id))
        avaliacao_existente = cursor.fetchone()

        if avaliacao_existente:
            # Se a avaliação já existe, atualize-a
            cursor.execute(
                'UPDATE avaliacoes SET classificacao = ?, comentario = ? WHERE pedido_id = ? AND usuario_id = ?',
                (classificacao, comentario, pedido_id, usuario_id))
        else:
            # Se a avaliação não existe, insira uma nova
            cursor.execute(
                'INSERT INTO avaliacoes (pedido_id, usuario_id, classificacao, comentario) VALUES (?, ?, ?, ?)',
                (pedido_id, usuario_id, classificacao, comentario))

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print('Erro ao salvar avaliação do item do pedido no banco de dados:', str(e))


def obter_pedidos_realizados():
    try:
        conn = sqlite3.connect('app.db')  # Substitua 'app.db' pelo nome do seu banco de dados
        cursor = conn.cursor()

        # Consulta SQL para obter os pedidos já realizados e os cupcakes relacionados
        cursor.execute('''
            SELECT 
                pedidos.id AS pedido_id, 
                pedidos.usuario_id, 
                pedidos.data_pedido, 
                pedidos.status, 
                itens_pedido.id AS item_pedido_id,
                cupcakes.id AS cupcake_id,
                cupcakes.nome AS cupcake_nome,
                cupcakes.descricao AS cupcake_descricao,
                cupcakes.preco AS cupcake_preco,
                cupcakes.imagem_url AS cupcake_imagem_url,
                itens_pedido.quantidade
            FROM pedidos
            JOIN itens_pedido ON pedidos.id = itens_pedido.pedido_id
            JOIN cupcakes ON itens_pedido.cupcake_id = cupcakes.id
            WHERE pedidos.status = 'Concluído'
        ''')
        pedidos_data = cursor.fetchall()

        pedidos = []

        for pedido_data in pedidos_data:
            pedido_id = pedido_data[0]

            # Verifique se o pedido já está na lista de pedidos
            pedido_existente = next((pedido for pedido in pedidos if pedido['id'] == pedido_id), None)

            if not pedido_existente:
                # Se o pedido não existe na lista, crie um novo registro
                pedido = {
                    'id': pedido_id,
                    'usuario_id': pedido_data[1],
                    'data_pedido': pedido_data[2],
                    'status': pedido_data[3],
                    'itens': []  # Uma lista para armazenar os itens relacionados a este pedido
                }
                pedidos.append(pedido)
            else:
                pedido = pedido_existente

            # Crie um registro para o item de pedido e cupcakes relacionados
            item_pedido = {
                'id': pedido_data[4],  # ID do item de pedido
                'cupcake': {
                    'id': pedido_data[5],
                    'nome': pedido_data[6],
                    'descricao': pedido_data[7],
                    'preco': pedido_data[8],
                    'imagem_url': pedido_data[9]
                },
                'quantidade': pedido_data[10]
            }

            # Adicione o item de pedido à lista de itens do pedido
            pedido['itens'].append(item_pedido)

        conn.commit()
        conn.close()
        return pedidos
    except sqlite3.Error as e:
        print('Erro ao buscar pedidos realizados:', str(e))

    return []


@app.route('/obter_detalhes_pedido', methods=['GET'])
def obter_detalhes_pedido():
    pedido_id = request.args.get('pedido_id')
    # Suponha que você tenha uma função que retorne os detalhes do pedido com base no pedido_id
    pedido_detalhes = buscar_detalhes_pedido(pedido_id)

    if pedido_detalhes:
        # Renderize os detalhes do pedido em HTML
        html_detalhes_pedido = renderizar_detalhes_pedido(pedido_detalhes)
        return html_detalhes_pedido

    # Se o pedido não for encontrado, você pode retornar uma mensagem de erro
    return 'Pedido não encontrado', 404


def renderizar_detalhes_pedido(pedido_detalhes):
    # Aqui você pode formatar os detalhes do pedido em HTML
    html = '<h2>Detalhes do Pedido</h2>'
    html += f'<p>ID do Pedido: {pedido_detalhes["id"]}</p>'
    html += f'<p>Cliente: {pedido_detalhes["cliente"]}</p>'
    html += f'<p>Endereço: {pedido_detalhes["endereco"]}</p>'

    html += '<h3>Itens do Pedido</h3>'
    html += '<ul>'
    for item in pedido_detalhes['itens']:
        html += f'<li>Nome: {item["nome"]},Descricao: {item["descricao"]}, Preço Unitário: R$ {item["preco_unitario"]}, Quantidade: {item["quantidade"]}</li>'
    html += '</ul>'

    # Você pode adicionar mais informações conforme necessário

    return html


# Função para buscar detalhes do pedido (exemplo)
def buscar_detalhes_pedido(pedido_id):
    try:
        conn = sqlite3.connect('app.db')  # Substitua pelo nome do seu banco de dados
        cursor = conn.cursor()

        # Consulta SQL para buscar detalhes do pedido com base no pedido_id
        cursor.execute('''
            SELECT 
                pedidos.id AS pedido_id, 
                pedidos.usuario_id, 
                pedidos.data_pedido, 
                pedidos.status, 
                itens_pedido.id AS item_pedido_id,
                cupcakes.id AS cupcake_id,
                cupcakes.nome AS cupcake_nome,
                cupcakes.descricao AS cupcake_descricao,
                cupcakes.preco AS cupcake_preco,
                cupcakes.imagem_url AS cupcake_imagem_url,
                itens_pedido.quantidade
            FROM pedidos
            JOIN itens_pedido ON pedidos.id = itens_pedido.pedido_id
            JOIN cupcakes ON itens_pedido.cupcake_id = cupcakes.id
            WHERE pedidos.id = ?
        ''', (pedido_id,))

        detalhes_pedido = {
            'itens': []
        }

        for row in cursor.fetchall():
            detalhes_pedido['id'] = row[0]
            detalhes_pedido['cliente'] = row[4]
            detalhes_pedido['endereco'] = row[5]
            detalhes_item = {
                'nome': row[6],
                'quantidade': row[10],
                'preco_unitario': row[8],
                'descricao': row[7]
            }
            detalhes_pedido['itens'].append(detalhes_item)

        conn.commit()
        conn.close()
        return detalhes_pedido

    except sqlite3.Error as e:
        print('Erro ao buscar detalhes do pedido:', str(e))
        return None


def obter_pedidos_por_usuario(usuario_id):
    try:
        conn = sqlite3.connect('app.db')  # Substitua pelo nome do seu banco de dados
        cursor = conn.cursor()

        # Consulta SQL para buscar detalhes dos pedidos do usuário com base no usuario_id
        cursor.execute('''
            SELECT 
                pedidos.id AS pedido_id, 
                pedidos.usuario_id, 
                pedidos.data_pedido, 
                pedidos.status, 
                itens_pedido.id AS item_pedido_id,
                cupcakes.id AS cupcake_id,
                cupcakes.nome AS cupcake_nome,
                cupcakes.descricao AS cupcake_descricao,
                cupcakes.preco AS cupcake_preco,
                cupcakes.imagem_url AS cupcake_imagem_url,
                itens_pedido.quantidade
            FROM pedidos
            JOIN itens_pedido ON pedidos.id = itens_pedido.pedido_id
            JOIN cupcakes ON itens_pedido.cupcake_id = cupcakes.id
            WHERE pedidos.usuario_id = ?
        ''', (usuario_id,))

        detalhes_pedidos = []

        for row in cursor.fetchall():
            detalhes_pedido = {
                'pedido_id': row[0],
                'usuario_id': row[1],
                'data_pedido': row[2],
                'status': row[3],
                'item_pedido_id': row[4],
                'cupcake_id': row[5],
                'cupcake_nome': row[6],
                'cupcake_descricao': row[7],
                'cupcake_preco': row[8],
                'cupcake_imagem_url': row[9],
                'quantidade': row[10]
            }
            detalhes_pedidos.append(detalhes_pedido)

        conn.commit()
        conn.close()
        return detalhes_pedidos

    except sqlite3.Error as e:
        print('Erro ao buscar detalhes dos pedidos do usuário:', str(e))
        return None


@app.route('/obter_pedidos_avaliados', methods=['GET'])
def obter_pedidos_avaliados():
    usuario_id = session['usuario_id']
    print("USER = ", usuario_id)
    try:
        # Conecte-se ao banco de dados SQLite (substitua 'app.db' pelo nome do seu banco de dados)
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        # Consulte o banco de dados para obter todos os pedidos do usuário especificado
        cursor.execute('SELECT pedido_id, comentario, classificacao FROM avaliacoes WHERE usuario_id = ?',
                       (usuario_id,))

        # Recupere todos os pedidos do usuário
        pedidos = cursor.fetchall()
        print(pedidos)
        # Feche a conexão com o banco de dados
        conn.commit()
        conn.close()

        # Converta os resultados em um formato JSON e retorne-os como resposta
        return jsonify(pedidos)

    except sqlite3.Error as e:
        return jsonify({'mensagem': 'Erro no banco de dados'}), 500


    except sqlite3.Error as e:
        return jsonify({'mensagem': 'Erro no banco de dados'}), 500


@app.route('/listar_pedidos', methods=['GET'])
def listar_pedidos():
    # Recupere o 'usuario_id' do usuário logado da sessão (você pode ter um sistema de autenticação para definir isso)
    usuario_id = session.get('usuario_id')

    if usuario_id is None:
        # O usuário não está autenticado, você pode redirecioná-lo para uma página de login
        return redirect('/login')  # Substitua '/login' pela rota real da página de login

    # Aqui, você deve recuperar os pedidos do banco de dados que estão vinculados ao 'usuario_id'
    # Suponha que você tenha uma função chamada 'obter_pedidos_por_usuario' que retorna uma lista de pedidos vinculados ao usuário

    pedidos = obter_pedidos_por_usuario(usuario_id)  # Substitua esta linha pela chamada à função apropriada

    return render_template('avaliar_item_pedido.html', pedidos=pedidos)


@app.route('/avaliar_item_pedido/<int:pedido_id>/<int:cupcake_id>', methods=['GET', 'POST'])
def avaliar_item_pedido(pedido_id, cupcake_id):
    # Verifique se o usuário está autenticado
    if 'usuario_id' not in session:
        flash('Faça o login para avaliar itens do pedido.', 'error')
        return redirect(url_for('login'))

    # Recupere informações do item do pedido
    item_pedido = obter_item_pedido_por_ids(pedido_id, cupcake_id)

    # Verifique se o item do pedido existe e pertence ao usuário logado
    if not item_pedido or item_pedido['usuario_id'] != session['usuario_id']:
        flash('Item do pedido não encontrado ou não autorizado para avaliação.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        classificacao = int(request.form.get('classificacao'))
        comentario = request.form.get('comentario')

        # Valide os dados do formulário aqui

        # Salve a avaliação do item do pedido no banco de dados (supondo que você tenha uma função para fazer isso)
        salvar_avaliacao_item_pedido(pedido_id, cupcake_id, classificacao, comentario)

        flash('Item do pedido avaliado com sucesso.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('avaliar_item_pedido.html', item_pedido=item_pedido)


@app.route('/inserir_avaliacao', methods=['POST'])
def inserir_avaliacao():
    data = request.json
    print(data)
    pedido_id = data.get('pedido_id')
    classificacao = data.get('classificacao')
    comentario = data.get('comentario')
    usuario_id = data.get('usuario_id')

    if pedido_id is not None and comentario is not None:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO avaliacoes (pedido_id, classificacao, comentario, usuario_id) VALUES (?, ?, ?,?)',
                       (pedido_id, classificacao, comentario, usuario_id))
        conn.commit()
        conn.close()

        # Responda com um JSON para indicar o sucesso
        return jsonify({'message': 'Avaliação inserida com sucesso'}), 200
    else:
        # Responda com um JSON para indicar um erro
        return jsonify({'error': 'Dados de avaliação inválidos'}), 400


@app.route('/avaliacoes_pedido/<int:pedido_id>/<int:usuario_id>')
def obter_avaliacoes_pedido(pedido_id, usuario_id):
    conn = sqlite3.connect('app.db')
    print("Usuario ID:", usuario_id)
    cursor = conn.cursor()
    cursor.execute('SELECT classificacao, comentario FROM avaliacoes WHERE pedido_id = ? AND usuario_id = ?',
                   (pedido_id, usuario_id,))
    avaliacoes = cursor.fetchall()
    conn.commit()
    conn.close()
    return jsonify(avaliacoes)


@app.route('/obter_usuario_id/<int:pedido_id>', methods=['GET'])
def obter_usuario_id(pedido_id):
    try:
        # Consulte o banco de dados fictício para obter o usuario_id com base no pedido_id
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT usuario_id FROM pedidos WHERE id = ?', (pedido_id,))
        usuario_info = cursor.fetchone()
        print(usuario_info)
        conn.commit()
        conn.close()

        if usuario_info:
            return jsonify({'usuario_id': usuario_info[0]})
        else:
            return jsonify({'mensagem': 'Pedido não encontrado'}), 404
    except sqlite3.Error as e:
        return jsonify({'mensagem': 'Erro no banco de dados'}), 500

@app.route('/verificar_avaliacao/<int:pedido_id>', methods=['GET'])
def verificar_avaliacao(pedido_id):
    try:
        # Consulta SQL para verificar a avaliação com base no pedido_id
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id ,classificacao, comentario FROM avaliacoes WHERE pedido_id = ?', (pedido_id,))
        resultado = cursor.fetchone()

        conn.commit()
        conn.close()

        if resultado:
            # Se houver uma avaliação, retorna a classificação e o comentário
            id, classificacao, comentario = resultado
            print(resultado)
            return jsonify({'avaliacao_id': id, 'classificacao': classificacao, 'comentario': comentario})
        else:
            # Se não houver uma avaliação, retorne None (ou um valor apropriado)
            return jsonify(None)
    except sqlite3.Error as e:
        # Lida com erros de banco de dados
        return jsonify({'error': str(e)})

@app.route('/atualizar_avaliacao/<int:avaliacao_id>', methods=['PUT'])
def atualizar_avaliacao(avaliacao_id):
    try:
        # Verifique se a avaliação com o ID especificado existe
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM avaliacoes WHERE id = ?', (avaliacao_id,))
        avaliacao = cursor.fetchone()
        print(avaliacao)

        if not avaliacao:
            return jsonify({'error': 'Avaliação não encontrada'}), 404

        # Recupere os novos dados da avaliação do corpo da solicitação
        novo_classificacao = request.json.get('classificacao')
        novo_comentario = request.json.get('comentario')
        print(novo_classificacao)
        print(novo_comentario)

        # Atualize os dados da avaliação no banco de dados
        cursor.execute('''
            UPDATE avaliacoes
            SET classificacao = ?, comentario = ?
            WHERE id = ?
        ''', (novo_classificacao, novo_comentario, avaliacao_id))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Avaliação atualizada com sucesso'})

    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
