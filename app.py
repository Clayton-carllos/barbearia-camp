from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import csv
from io import StringIO
from flask import Response
from flask_migrate import Migrate
from sqlalchemy import and_

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
        ((Agendamento.data == agora.date()) & (Agendamento.horario > agora.strftime('%H:%M')))
    ).count()
    
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
    agendamentos_mes = Agendamento.query.filter(extract('month', Agendamento.data) == mes_atual).count()
    
    # Pega os 3 próximos agendamentos
    proximos_agendamentos = (
        Agendamento.query
        .filter(
            (Agendamento.data > datetime.today().date()) | 
            ((Agendamento.data == datetime.today().date()) & (Agendamento.horario > agora.strftime('%H:%M')))
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
