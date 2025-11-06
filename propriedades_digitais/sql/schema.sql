CREATE TABLE IF NOT EXISTS dono (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  cpf_cnpj TEXT NOT NULL UNIQUE,
  email TEXT,
  telefone TEXT
);

CREATE TABLE IF NOT EXISTS propriedade (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  municipio TEXT NOT NULL,
  estado TEXT NOT NULL,
  area_total_ha REAL NOT NULL CHECK (area_total_ha >= 0),
  dono_id INTEGER NOT NULL,
  FOREIGN KEY (dono_id) REFERENCES dono(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS cultura (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  especie TEXT,
  ciclo TEXT CHECK (ciclo IN ('Anual','Perene'))
);

CREATE TABLE IF NOT EXISTS cultivo (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  propriedade_id INTEGER NOT NULL,
  cultura_id INTEGER NOT NULL,
  area_cultivada_ha REAL NOT NULL CHECK (area_cultivada_ha >= 0),
  data_plantio DATE,
  data_colheita_prevista DATE,
  FOREIGN KEY (propriedade_id) REFERENCES propriedade(id) ON DELETE CASCADE,
  FOREIGN KEY (cultura_id) REFERENCES cultura(id) ON DELETE RESTRICT
);