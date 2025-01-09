from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract
from sqlalchemy import Time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import csv
from io import StringIO
from flask import Response
from flask_migrate import Migrate


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessário para usar flash()

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://agendamentos_db_cbsl_user:al4jVarr1TMQwCQPhJyTRLGScquVmkQa@dpg-ctvu5n0gph6c73cgbcdg-a.virginia-postgres.render.com/agendamentos_db_cbsl'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelo do banco de dados para agendamentos
class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    data = db.Column(db.Date, nullable=False)
    horario = db.Column(db.String(5), nullable=False)
    mensagem = db.Column(db.Text, nullable=True)

# Modelo de usuário para o login
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    senha = db.Column(db.String(200), nullable=False)

# Criar o banco de dados e verificar se o admin existe
with app.app_context():
    db.create_all()  # Certifica-se de que as tabelas existem no banco de dados

    # Verifica se já existe um usuário "admin"
    admin = Usuario.query.filter_by(username='admin').first()
    if not admin:
        # Criação do usuário admin caso não exista
        senha_hash = generate_password_hash('admin123')  # Senha padrão para o admin
        usuario_admin = Usuario(username='admin', senha=senha_hash)
        db.session.add(usuario_admin)
        db.session.commit()
        print('Usuário admin criado com sucesso!')
    else:
        print('Usuário admin já existe.')

# Rota para exibir o formulário de agendamento
@app.route('/')
def index():
    return render_template('formulario.html')

# Rota para processar o agendamento
@app.route('/agendar', methods=['POST'])
def agendar():
    nome = request.form['nome']
    telefone = request.form['telefone']
    email = request.form['email']
    data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
    horario = request.form['horario']
    mensagem = request.form.get('mensagem')

    # Criação de um novo agendamento
    novo_agendamento = Agendamento(
        nome=nome, telefone=telefone, email=email, data=data, horario=horario, mensagem=mensagem
    )

    # Salvar no banco de dados
    db.session.add(novo_agendamento)
    db.session.commit()

    # Mensagem flash para informar o sucesso
    flash('Agendamento realizado com sucesso!.', 'success')

    return redirect(url_for('index'))  # Redireciona de volta ao formulário

# Rota para exibir o formulário de adicionar usuário
@app.route('/adicionar_usuario', methods=['GET', 'POST'])
def adicionar_usuario():
    
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para adicionar um usuário.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        # Verificar se o username já existe
        if Usuario.query.filter_by(username=username).first():
            flash('O nome de usuário já está em uso. Escolha outro.', 'danger')
            return render_template('adicionar_usuario.html')

        # Criação do hash da senha
        senha_hash = generate_password_hash(senha)

        # Criar o novo usuário
        novo_usuario = Usuario(username=username, senha=senha_hash)

        try:
            # Adicionar ao banco de dados
            db.session.add(novo_usuario)
            db.session.commit()

            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('lista_usuarios'))  # Redireciona para a lista de usuários
        except IntegrityError:
            db.session.rollback()  # Desfaz a transação se ocorrer um erro
            flash('Erro ao criar o usuário. Tente novamente.', 'danger')

    return render_template('adicionar_usuario.html')  # Exibe o formulário para adicionar usuário

# Rota para editar um usuário
@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)  # Busca o usuário pelo ID
    if request.method == 'POST':
        # Atualiza os campos do usuário
        usuario.username = request.form['username']
        usuario.senha = generate_password_hash(request.form['senha'])  # Atualiza a senha com hash

        # Salva no banco de dados
        db.session.commit()

        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('lista_usuarios'))  # Redireciona para a lista de usuários

    return render_template('editar_usuario.html', usuario=usuario)  # Exibe o formulário de edição

# Rota para listar usuários
@app.route('/usuarios')
def lista_usuarios():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('login'))
    
    # Recupera o nome do usuário logado
    nome_usuario = session.get('username')  # Obtém o nome do usuário da sessão

    usuarios = Usuario.query.all()  # Recupera todos os usuários do banco de dados
    return render_template('lista_usuarios.html', usuarios=usuarios, nome_usuario=nome_usuario)

# Rota para exibir o perfil de um usuário
@app.route('/usuario/<int:id>')
def perfil_usuario(id):
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('login'))

    usuario = Usuario.query.get_or_404(id)  # Recupera o usuário pelo ID
    return render_template('perfil_usuario.html', usuario=usuario)

# Rota para deletar um usuário
@app.route('/deletar_usuario/<int:id>', methods=['GET'])
def deletar_usuario(id):
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para realizar esta ação.', 'warning')
        return redirect(url_for('login'))

    usuario = Usuario.query.get_or_404(id)  # Recupera o usuário pelo ID
    db.session.delete(usuario)  # Exclui o usuário
    db.session.commit()  # Salva a mudança no banco de dados
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('lista_usuarios'))  # Redireciona para a lista de usuários

# Rota para exibir a página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario and check_password_hash(usuario.senha, senha):
            session['usuario_id'] = usuario.id
            session['username'] = usuario.username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    
    return render_template('login.html')

# Rota para exibir a lista de agendamentos
@app.route('/agendamentos')
def lista_agendamentos():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('login'))
    
    # Recupera o nome do usuário logado
    nome_usuario = session.get('username')  # Obtém o nome do usuário da sessão

    filtro = request.args.get('filtro', default=None)
    
    if filtro == 'hoje':
        # Filtra apenas os agendamentos de hoje
        agendamentos = Agendamento.query.filter(Agendamento.data == datetime.today().date()).all()
    else:
        # Caso contrário, exibe todos os agendamentos
        agendamentos = Agendamento.query.all()

    return render_template('lista_agendamentos.html', agendamentos=agendamentos, nome_usuario=nome_usuario)

# Rota para exibir a Home
@app.route('/home')
def home():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('login'))
    
    nome_usuario = session.get('username')  # Nome do usuário logado
    
    # Total de agendamentos
    total_agendamentos = Agendamento.query.count()

    # Pega a data e hora atuais
    agora = datetime.now()
    
    # Agendamentos futuros
    agendamentos_futuros = Agendamento.query.filter(
        (Agendamento.data > agora.date()) | 
        ((Agendamento.data == agora.date()) & (Agendamento.horario > agora.time()))
    ).all()
    
    # Definir o início e o fim da semana (de segunda a domingo)
    inicio_semana = agora - timedelta(days=agora.weekday())  # Começa na segunda-feira
    fim_semana = inicio_semana + timedelta(days=6)  # Termina no domingo
    
    # Filtra os agendamentos da semana atual (segunda a domingo)
    agendamentos_semana = Agendamento.query.filter(
        Agendamento.data >= inicio_semana.date(),
        Agendamento.data <= fim_semana.date()
    ).all()

    # Calcular a média semanal de agendamentos
    total_agendamentos_semana = len(agendamentos_semana)
    dias_na_semana = 7  # Considera sempre 7 dias
    media_semanal = total_agendamentos_semana / dias_na_semana if dias_na_semana > 0 else 0

    # Contagem de agendamentos no mês
    mes_atual = agora.month
    agendamentos_mes = Agendamento.query.filter(
        extract('month', Agendamento.data) == mes_atual
    ).count()
    
    # Pega os 3 próximos agendamentos
    proximos_agendamentos = (
        Agendamento.query
        .filter(
            (Agendamento.data > agora.date()) | 
            ((Agendamento.data == agora.date()) & (Agendamento.horario > agora.time()))
        )
        .order_by(Agendamento.data, Agendamento.horario)
        .limit(3)
        .all()
    )

    return render_template(
        'home.html', 
        total_agendamentos=total_agendamentos, 
        agendamentos_futuros=agendamentos_futuros,
        media_semanal=media_semanal,
        nome_usuario=nome_usuario,
        agendamentos_mes=agendamentos_mes,
        proximos_agendamentos=proximos_agendamentos
    )


# Rota para deletar um agendamento
@app.route('/deletar/<int:id>')
def deletar(id):
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para realizar esta ação.', 'warning')
        return redirect(url_for('login'))

    agendamento = Agendamento.query.get_or_404(id)  # Recupera o agendamento pelo ID
    db.session.delete(agendamento)  # Exclui o agendamento
    db.session.commit()  # Salva a mudança no banco de dados
    flash('Agendamento excluído com sucesso!', 'success')
    return redirect(url_for('lista_agendamentos'))  # Redireciona para a lista de agendamentos

# Rota para horários indisponíveis
@app.route('/horarios_indisponiveis', methods=['GET'])
def horarios_indisponiveis():
    data = request.args.get('data')  # Pega a data enviada na requisição
    if not data:
        return {"error": "Data não fornecida."}, 400

    try:
        data_obj = datetime.strptime(data, '%Y-%m-%d').date()
    except ValueError:
        return {"error": "Formato de data inválido."}, 400

    # Consulta os horários ocupados para a data específica
    agendamentos = Agendamento.query.filter_by(data=data_obj).all()
    horarios = [agendamento.horario for agendamento in agendamentos]

    return {"horarios_indisponiveis": horarios}

@app.route('/exportar-relatorio')
def exportar_relatorio():
    # Pega todos os agendamentos
    agendamentos = Agendamento.query.all()

    # Cria um buffer de StringIO para armazenar o CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Escreve o cabeçalho do CSV
    writer.writerow(['Cliente', 'Data', 'Horario', 'Mensagem'])

    # Adiciona os dados dos agendamentos ao CSV
    for agendamento in agendamentos:
        writer.writerow([agendamento.nome, agendamento.data.strftime('%d/%m/%Y'), agendamento.horario, agendamento.mensagem])
    
    # Prepara o CSV para ser enviado como resposta
    output.seek(0)  # Volta o ponteiro do buffer para o início
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=relatorio_agendamentos.csv"}
    )

# Rota para logout
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('usuario_id', None)  # Remove a sessão do usuário
    session.pop('username', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))  # Redireciona para a página de login

if __name__ == "__main__":
    app.run(debug=True)
