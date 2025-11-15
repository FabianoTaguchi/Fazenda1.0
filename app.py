from flask import Flask, render_template, request
from flask import redirect, url_for, flash, session
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Configuração da aplicação e do banco de dados
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:root@localhost:3306/progest2?charset=utf8mb4')
db = SQLAlchemy(app)

#ORM para manipulação das tabelas
class Dono(db.Model):
    __tablename__ = 'dono'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    cpf_cnpj = db.Column(db.String(18), nullable=False, unique=True)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
class Propriedade(db.Model):
    __tablename__ = 'propriedade'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    municipio = db.Column(db.String(80), nullable=False)
    estado = db.Column(db.String(80), nullable=False)
    area_total_ha = db.Column(db.Numeric(10, 2), nullable=False)
    # Relacionamento com o atributo id da tabela Dono
    dono_id = db.Column(db.Integer, db.ForeignKey('dono.id'), nullable=False)
    # Relacionamento com a tabela dono
    dono = db.relationship('Dono', backref='propriedades')
class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column('password', db.String(255), nullable=False)
class Animal(db.Model):
    __tablename__ = 'animal'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(80), nullable=False)
    raca = db.Column(db.String(80))
class Lote(db.Model):
    __tablename__ = 'lote'
    id = db.Column(db.Integer, primary_key=True)
    # Relacionamento com as tabelas propriedade e animal
    propriedade_id = db.Column(db.Integer, db.ForeignKey('propriedade.id'), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data_registro = db.Column(db.Date)

# Rotas principal da aplicação
@app.route('/index')
def index():
    return render_template('index.html', show_menu=True)

# Rota que lista os proprietários cadastrados
@app.route('/owners', methods=['GET'])
def owners():
    try:
        donos_q = Dono.query.order_by(Dono.id.desc()).all()
        # Ajuste para chaves usadas no template owners.html
        donos = [{
                'id_proprietario': d.id,
                'nome': d.nome,
                'cpf': d.cpf_cnpj,
                'email': d.email,
                'telefone': d.telefone,
            } for d in donos_q
        ]
    except Exception as e:
        flash(f'Erro ao carregar proprietários: {e}', 'danger')
    return render_template('owners.html', donos=donos, show_menu=True)

# Rota que recebe os dados do formulário e cadastra um proprietário
@app.route('/owners/cadastrar', methods=['POST'])
def cadastrarProprietario():
    nome = (request.form.get('nome') or '').strip()
    cpf_cnpj = (request.form.get('cpf_cnpj') or '').strip()
    telefone = (request.form.get('telefone') or '').strip()
    email = (request.form.get('email') or '').strip()

    # Verifica se o login ou o nome estão em branco
    if not nome or not cpf_cnpj:
        flash('Campo nome e cpf/cnpj são obrigatórios', 'warning')
        return redirect(url_for('owners'))

    try:
        novo = Dono(nome=nome, cpf_cnpj=cpf_cnpj, telefone=telefone, email=email)
        db.session.add(novo)
        db.session.commit()
        flash('Proprietário cadastrado com sucesso.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('CPF/CNPJ já cadastrado.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cadastrar proprietário: {e}', 'danger')
    return redirect(url_for('owners'))

# Rota que recebe os dados de uma propriedade e cadastra
# A rota ao final também lista as propriedades cadastradas
@app.route('/propriedades', methods=['GET', 'POST'])
def propriedades():
    # POST: cadastra propriedade; GET: lista donos e propriedades
    if request.method == 'POST':
        # Lê os dados do formulário
        nome = (request.form.get('nome') or '').strip()
        municipio = (request.form.get('municipio') or '').strip()
        estado = (request.form.get('estado') or '').strip()
        area_total = request.form.get('area_total')
        dono_id = request.form.get('dono_id')
        # Valida campos obrigatórios
        if not nome or not municipio or not estado or not area_total or not dono_id:
            flash('Preencha todos os campos.', 'warning')
        else:
            try:
                # Cria o objeto prop a partir da classe Propriedade
                prop = Propriedade(
                    nome=nome,
                    municipio=municipio,
                    estado=estado,
                    area_total_ha=area_total,
                    dono_id=int(dono_id))
                db.session.add(prop)
                db.session.commit()
                flash('Propriedade cadastrada com sucesso.', 'success')
            except Exception as e:
                # Em caso de erro, desfaz transação e informa
                db.session.rollback()
                flash(f'Erro ao cadastrar propriedade: {e}', 'danger')
        # Redireciona para evitar reenvio do formulário ao atualizar a página
        return redirect(url_for('propriedades'))

    # Carrega os dados dos donos para popular o select do formulário
    try:
        donos_q = Dono.query.order_by(Dono.nome.asc()).all()
        donos = [{'id': d.id, 'nome': d.nome} for d in donos_q]
    except Exception as e:
        flash(f'Erro ao carregar proprietários: {e}', 'danger')
    # Consulta propriedades junto com o nome do dono que foi recuperado a partir de um join
    try:
        props_q = db.session.query(Propriedade, Dono).join(Dono, Propriedade.dono_id == Dono.id).order_by(Propriedade.nome.asc()).all()
        props = [{
                'nome': p.nome,
                'municipio': p.municipio,
                'estado': p.estado,
                'area_total_ha': float(p.area_total_ha),
                'dono_nome': d.nome,}
            for (p, d) in props_q]
    except Exception as e:
        flash(f'Erro ao carregar propriedades: {e}', 'danger')
    # Renderiza template com os dados para formulário e listagem
    return render_template('propriedades.html', donos=donos, propriedades=props, show_menu=True)

# Rota que recebe os dados de um animal e cadastra
# A rota ao final também lista os animais cadastrados
@app.route('/animais', methods=['GET', 'POST'])
def animais():
    if request.method == 'POST':
        tipo = (request.form.get('tipo') or '').strip()
        raca = (request.form.get('raca') or '').strip()
        if not tipo:
            flash('Informe o tipo do animal.', 'warning')
        else:
            try:
                novo = Animal(tipo=tipo, raca=raca or None)
                db.session.add(novo)
                db.session.commit()
                flash('Animal cadastrado com sucesso.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar animal: {e}', 'danger')
        return redirect(url_for('animais'))

    lista = []
    try:
        registros = Animal.query.order_by(Animal.tipo.asc()).all()
        lista = [{ 'tipo': a.tipo, 'raca': a.raca } for a in registros]
    except Exception as e:
        flash(f'Erro ao carregar animais: {e}', 'danger')
    return render_template('animais.html', animais=lista, show_menu=True)

# Rota que recebe os dados de um lote de animais e cadastra
# A rota ao final também lista dos lotes cadastrados
@app.route('/lotes', methods=['GET', 'POST'])
def lotes():
    # POST: cadastra lote; GET: carrega selects e lista lotes
    if request.method == 'POST':
        # Lê dados do formulário
        propriedade_id = request.form.get('propriedade_id')
        animal_id = request.form.get('animal_id')
        quantidade = request.form.get('quantidade')
        data_registro_str = request.form.get('data_registro')
        # Valida campos obrigatórios
        if not propriedade_id or not animal_id or not quantidade:
            flash('Informe propriedade, animal e quantidade.', 'warning')
            return redirect(url_for('lotes'))
        try:
            qnt = int(quantidade)
            # Converte data (YYYY-MM-DD) para objeto date
            data_registro_val = None
            if data_registro_str:
                try:
                    data_registro_val = datetime.strptime(data_registro_str, '%Y-%m-%d').date()
                except Exception:
                    data_registro_val = None

            # Cria o objeto novo a partir da classe Lote
            novo = Lote(
                propriedade_id=int(propriedade_id),
                animal_id=int(animal_id),
                quantidade=qnt,
                data_registro=data_registro_val
            )
            db.session.add(novo)
            db.session.commit()
            flash('Lote registrado com sucesso.', 'success')
        except Exception as e:
            # Em caso de erro, desfaz transação e informa
            db.session.rollback()
            flash(f'Erro ao registrar lote: {e}', 'danger')
        # Redireciona para evitar reenvio do formulário
        return redirect(url_for('lotes'))

    propriedades = []
    animais = []
    lotes = []
    try:
        # Carrega propriedades para o select
        ps = Propriedade.query.order_by(Propriedade.nome.asc()).all()
        propriedades = [{ 'id': p.id, 'nome': p.nome } for p in ps]
    except Exception as e:
        flash(f'Erro ao carregar propriedades: {e}', 'danger')
    try:
        # Carrega animais para o select (exibe "tipo - raça")
        as_ = Animal.query.order_by(Animal.tipo.asc()).all()
        animais = [{ 'id': a.id, 'descricao': f"{a.tipo} - {a.raca}" if a.raca else a.tipo } for a in as_]
    except Exception as e:
        flash(f'Erro ao carregar animais: {e}', 'danger')
    try:
        # Consulta lotes com join de Propriedade e Animal para montar a listagem
        registros = (
            db.session.query(Lote, Propriedade, Animal)
            .join(Propriedade, Lote.propriedade_id == Propriedade.id)
            .join(Animal, Lote.animal_id == Animal.id)
            .order_by(Propriedade.nome.asc(), Animal.tipo.asc())
            .all()
        )
        # Prepara os dados para o template (inclui data dd-mm-aaaa)
        lotes = [
            {
                'propriedade': prop.nome,
                'animal': f"{ani.tipo} - {ani.raca}" if ani.raca else ani.tipo,
                'quantidade': lt.quantidade,
                'data_registro': lt.data_registro.strftime('%d-%m-%Y') if lt.data_registro else None
            }
            for (lt, prop, ani) in registros
        ]
    except Exception as e:
        flash(f'Erro ao carregar lotes: {e}', 'danger')
    # Renderiza template com dados para formulário e listagem
    return render_template('lotes.html', propriedades=propriedades, animais=animais, lotes=lotes, show_menu=True)

# Rota principal que exibe a página de login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Informe usuário e senha.', 'warning')
            return redirect(url_for('login'))
        try:
            user = Usuario.query.filter_by(username=username).first()
            if not user or user.password != password:
                flash('Usuário ou senha inválidos.', 'danger')
                return redirect(url_for('login'))
            session['user'] = username
            flash('Login efetuado com sucesso.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Erro ao validar login: {e}', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html', show_menu=False)

# Rota usado para receber os dados do usuário e fazer o cadastro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '')
        if not username or not password:
            flash('Informe usuário e senha para criar a conta.', 'warning')
            return redirect(url_for('register'))
        try:
            exists = Usuario.query.filter_by(username=username).first()
            if exists:
                flash('Usuário já existe. Escolha outro.', 'warning')
                return redirect(url_for('register'))
            novo = Usuario(username=username, password=password)
            db.session.add(novo)
            db.session.commit()
            flash('Conta criada com sucesso. Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {e}', 'danger')
            return redirect(url_for('register'))
    return render_template('register.html', show_menu=False)

# Rota que faz o logout da aplicação
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Você saiu da aplicação.', 'info')
    return redirect(url_for('login'))


# Verifica se o arquivo é o principal do projeto
if __name__ == '__main__':
    # Cria tabelas se necessário e executa a aplicação
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5600'))
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print('Aviso: não foi possível criar tabelas automaticamente:', e)
    app.run(host=host, port=port, debug=True)
