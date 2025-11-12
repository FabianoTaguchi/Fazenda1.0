from flask import Flask, render_template, request
from flask import redirect, url_for, flash, session
from functools import wraps
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)

app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:root@localhost:3306/progest2?charset=utf8mb4')
db = SQLAlchemy(app)

class Proprietario(db.Model):
    __tablename__ = 'proprietario'
    id_proprietario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(80),nullable=True)
    cpf = db.Column(db.String(80), unique=True, nullable=True)
    telefone = db.Column(db.String(80))
    email = db.Column(db.String(80), unique=True)

@app.route('/index')
def index():
    return render_template('index.html', show_menu=True)

@app.route('/owners', methods=['GET'])
def owners():
    prop = Proprietario.query.order_by(Proprietario.id_proprietario.asc()).all()
    return render_template('owners.html',donos=prop, show_menu=True)

@app.route('/owners/cadastrar', methods=['POST'])
def cadastrarProprietario():
    nome = (request.form.get('nome') or '').strip()
    cpf_cnpj = (request.form.get('cpf_cnpj') or '').strip()
    telefone = (request.form.get('telefone') or '').strip()
    email = (request.form.get('email') or '').strip()

    # Verifica se o login ou o nome estão em branco
    if not nome or not cpf_cnpj:
        flash('Campo nome e cpf/cnpj são obrigatórios', 'warning')
        return redirect(url_for('index'))

    # Pega as variáveis e adiciona um novo usuário na tabela
    try:
        prop = Proprietario(
            nome=nome,
            cpf=cpf_cnpj,
            telefone=telefone or None,
            email=email or None)
        db.session.add(prop)
        db.session.commit()
        flash('Proprietário cadastrado com sucesso!', 'success')
        return redirect(url_for('index'))
    
    except IntegrityError:
        db.session.rollback()
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cadastrar: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/propriedades', methods=['GET'])
def propriedades():
    donos = []
    props = []
    return render_template('propriedades.html', donos=donos, propriedades=props, show_menu=True)

@app.route('/culturas', methods=['GET'])
def culturas():
    culturas = []
    return render_template('culturas.html', culturas=culturas, show_menu=True)

@app.route('/cultivos', methods=['GET'])
def cultivos():
    propriedades = []
    culturas = []
    cultivos = []
    return render_template('cultivos.html', propriedades=propriedades, culturas=culturas, cultivos=cultivos, show_menu=True)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Informe usuário e senha.', 'warning')
            return redirect(url_for('login'))
        
        # Aceita qualquer combinação por enquanto
        flash('Login aceito.', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', show_menu=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html', show_menu=False)

# Verifica se o arquivo é o principal do projeto
if __name__ == '__main__':
    # Runner da aplicação (configurável via env HOST/PORT)
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5600'))
    app.run(host=host, port=port, debug=True)
