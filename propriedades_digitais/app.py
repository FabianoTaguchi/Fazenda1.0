import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-key-change-me'

    base_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(base_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    app.config['DATABASE'] = os.path.join(instance_dir, 'rural.db')

    @app.before_request
    def before_request():
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row

    @app.teardown_request
    def teardown_request(exception):
        db = getattr(g, 'db', None)
        if db is not None:
            db.close()

    def init_db():
        schema_path = os.path.join(base_dir, 'sql', 'schema.sql')
        with app.open_resource(schema_path, mode='r') as f:
            g.db.executescript(f.read())
        g.db.commit()

    @app.route('/initdb')
    def initdb_route():
        init_db()
        flash('Banco inicializado com sucesso.', 'success')
        return redirect(url_for('index'))

    @app.route('/')
    def index():
        return render_template('index.html')

    # Donos
    @app.route('/owners', methods=['GET', 'POST'])
    def owners():
        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            cpf_cnpj = request.form.get('cpf_cnpj', '').strip()
            email = request.form.get('email', '').strip()
            telefone = request.form.get('telefone', '').strip()

            if not nome or not cpf_cnpj:
                flash('Nome e CPF/CNPJ são obrigatórios', 'warning')
                return redirect(url_for('owners'))
            try:
                g.db.execute(
                    'INSERT INTO dono (nome, cpf_cnpj, email, telefone) VALUES (?, ?, ?, ?)',
                    (nome, cpf_cnpj, email, telefone)
                )
                g.db.commit()
                flash('Dono cadastrado com sucesso', 'success')
            except sqlite3.IntegrityError:
                flash('CPF/CNPJ já cadastrado', 'danger')
            return redirect(url_for('owners'))

        donos = g.db.execute('SELECT * FROM dono ORDER BY nome').fetchall()
        return render_template('owners.html', donos=donos)

    # Propriedades
    @app.route('/propriedades', methods=['GET', 'POST'])
    def propriedades():
        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            municipio = request.form.get('municipio', '').strip()
            estado = request.form.get('estado', '').strip().upper()
            area_total = request.form.get('area_total', '').strip()
            dono_id = request.form.get('dono_id')

            if not (nome and municipio and estado and area_total and dono_id):
                flash('Todos os campos são obrigatórios', 'warning')
                return redirect(url_for('propriedades'))
            try:
                area_val = float(area_total)
                if area_val < 0:
                    raise ValueError('Área negativa')
            except ValueError:
                flash('Área deve ser um número não negativo', 'warning')
                return redirect(url_for('propriedades'))

            try:
                g.db.execute(
                    'INSERT INTO propriedade (nome, municipio, estado, area_total_ha, dono_id) VALUES (?, ?, ?, ?, ?)',
                    (nome, municipio, estado, area_val, int(dono_id))
                )
                g.db.commit()
                flash('Propriedade cadastrada com sucesso', 'success')
            except sqlite3.IntegrityError:
                flash('Falha ao cadastrar propriedade (verifique Dono válido)', 'danger')
            return redirect(url_for('propriedades'))

        donos = g.db.execute('SELECT id, nome FROM dono ORDER BY nome').fetchall()
        props = g.db.execute(
            'SELECT p.id, p.nome, p.municipio, p.estado, p.area_total_ha, d.nome as dono_nome '
            'FROM propriedade p JOIN dono d ON d.id = p.dono_id ORDER BY p.nome'
        ).fetchall()
        return render_template('propriedades.html', donos=donos, propriedades=props)

    # Culturas
    @app.route('/culturas', methods=['GET', 'POST'])
    def culturas():
        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            especie = request.form.get('especie', '').strip()
            ciclo = request.form.get('ciclo', '').strip() or None

            if not nome:
                flash('Nome da cultura é obrigatório', 'warning')
                return redirect(url_for('culturas'))

            g.db.execute(
                'INSERT INTO cultura (nome, especie, ciclo) VALUES (?, ?, ?)',
                (nome, especie or None, ciclo)
            )
            g.db.commit()
            flash('Cultura cadastrada com sucesso', 'success')
            return redirect(url_for('culturas'))

        culturas = g.db.execute('SELECT * FROM cultura ORDER BY nome').fetchall()
        return render_template('culturas.html', culturas=culturas)

    # Cultivos (associação Propriedade x Cultura)
    @app.route('/cultivos', methods=['GET', 'POST'])
    def cultivos():
        if request.method == 'POST':
            propriedade_id = request.form.get('propriedade_id')
            cultura_id = request.form.get('cultura_id')
            area_cultivada = request.form.get('area_cultivada')
            data_plantio = request.form.get('data_plantio') or None
            data_colheita = request.form.get('data_colheita') or None

            if not (propriedade_id and cultura_id and area_cultivada):
                flash('Propriedade, Cultura e Área são obrigatórios', 'warning')
                return redirect(url_for('cultivos'))
            try:
                area_val = float(area_cultivada)
                if area_val < 0:
                    raise ValueError('Área negativa')
            except ValueError:
                flash('Área cultivada deve ser número não negativo', 'warning')
                return redirect(url_for('cultivos'))

            try:
                g.db.execute(
                    'INSERT INTO cultivo (propriedade_id, cultura_id, area_cultivada_ha, data_plantio, data_colheita_prevista) '
                    'VALUES (?, ?, ?, ?, ?)',
                    (int(propriedade_id), int(cultura_id), area_val, data_plantio, data_colheita)
                )
                g.db.commit()
                flash('Cultivo cadastrado com sucesso', 'success')
            except sqlite3.IntegrityError:
                flash('Falha ao cadastrar cultivo (verifique Propriedade/Cultura válidas)', 'danger')
            return redirect(url_for('cultivos'))

        propriedades = g.db.execute('SELECT id, nome FROM propriedade ORDER BY nome').fetchall()
        culturas = g.db.execute('SELECT id, nome FROM cultura ORDER BY nome').fetchall()
        cultivos = g.db.execute(
            'SELECT c.id, p.nome AS propriedade, cu.nome AS cultura, c.area_cultivada_ha, c.data_plantio, c.data_colheita_prevista '
            'FROM cultivo c JOIN propriedade p ON p.id = c.propriedade_id JOIN cultura cu ON cu.id = c.cultura_id '
            'ORDER BY p.nome, cu.nome'
        ).fetchall()
        return render_template('cultivos.html', propriedades=propriedades, culturas=culturas, cultivos=cultivos)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5600, debug=False)