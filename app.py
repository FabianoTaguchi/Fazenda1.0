import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')

@app.route('/index')
def index():
    return render_template('index.html', show_menu=True)

@app.route('/owners', methods=['GET'])
def owners():
    donos = []
    return render_template('owners.html', donos=donos, show_menu=True)

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
