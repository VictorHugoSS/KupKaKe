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
        CREATE TABLE IF NOT EXISTS cupcakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco DECIMAL(10, 2) NOT NULL,
            disponivel BOOLEAN DEFAULT 1,
            imagem_url TEXT,
            data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        CREATE TABLE IF NOT EXIST compras(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            id_cupcake INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            data_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
            FOREIGN KEY (id_cupcake) REFERENCES cupcakes(id)
        );

    ''')

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

        conn.close()

        if usuario:
            session['usuario_id'] = usuario[0]
            #flash('Login bem-sucedido', 'success')

            # Verifique se o usuário é um administrador
            print("Valor do campo de administrador:", usuario[5])

            if usuario[5] == 1:  # Suponha que o campo que indica se é administrador seja o quarto campo na tabela (índice 3)
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
                return redirect(url_for('dashboard'))  # Redireciona para o painel normal se o usuário não for administrador
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
            flash('Este email já está associado a uma conta existente. Por favor, faça login ou use outro email.', 'error')
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

            #if cupcake_info:
                #print("Informações do Cupcake:")
                #print(cupcake_info)
            #else:
                #print("Cupcake não encontrado.")
            return cupcake_info

    except sqlite3.Error as e:
        # Tratar exceções de banco de dados, se necessário
        print("Erro ao buscar o cupcake:", e)
    finally:
        # Fechar a conexão com o banco de dados
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

# Rota para gerenciar o estoque de produtos
@app.route('/manage_stock')
def manage_stock():
    if 'usuario_id' in session:
        if session['tipo_usuario'] == 'administrador':
            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM produtos')
            produtos = cursor.fetchall()

            conn.close()

            return render_template('manage_stock.html', produtos=produtos)

    flash('Faça o login como administrador para gerenciar o estoque', 'error')
    return redirect(url_for('login'))

# Rota para o chat de suporte
@app.route('/support_chat')
def support_chat():
    return render_template('support_chat.html')

if __name__ == '__main__':
    app.run(debug=True)
