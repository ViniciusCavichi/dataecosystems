import json
import os
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('CLINICA_DB', str(ROOT / 'data' / 'clinica.db')))

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys = ON')
    return c

def init():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS clients (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, address TEXT DEFAULT '',
          age INTEGER, email TEXT DEFAULT '', phone TEXT DEFAULT '',
          instagram TEXT DEFAULT '', notes TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS appointments (
          id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
          starts_at TEXT NOT NULL, duration INTEGER NOT NULL DEFAULT 60,
          service TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Agendado', notes TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS records (
          id INTEGER PRIMARY KEY, client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
          date TEXT NOT NULL, procedure TEXT NOT NULL, evolution TEXT NOT NULL,
          recommendations TEXT DEFAULT '');
        ''')

TABLES = {
    'clients': ['name', 'address', 'age', 'email', 'phone', 'instagram', 'notes'],
    'appointments': ['client_id', 'starts_at', 'duration', 'service', 'status', 'notes'],
    'records': ['client_id', 'date', 'procedure', 'evolution', 'recommendations'],
}

def validate(table, d, c, row_id=None):
    required = {'clients': ['name'], 'appointments': ['client_id', 'starts_at', 'service'], 'records': ['client_id', 'date', 'procedure', 'evolution']}[table]
    for field in required:
        if not str(d.get(field) or '').strip():
            raise ValueError('Preencha todos os campos obrigatórios.')
    for k, v in d.items():
        if isinstance(v, str):
            d[k] = v.strip()
    if table == 'clients':
        age = d.get('age')
        d['age'] = None if age in ('', None) else int(age)
        if d['age'] is not None and not 0 <= d['age'] <= 120:
            raise ValueError('Informe uma idade entre 0 e 120.')
    else:
        if not c.execute('SELECT id FROM clients WHERE id=?', (d['client_id'],)).fetchone():
            raise ValueError('Cliente não encontrado.')
    if table == 'records':
        datetime.strptime(d['date'], '%Y-%m-%d')
    if table == 'appointments':
        start = datetime.strptime(d['starts_at'], '%Y-%m-%dT%H:%M')
        duration = int(d.get('duration', 60))
        if not 5 <= duration <= 480:
            raise ValueError('A duração deve ser de 5 a 480 minutos.')
        d['duration'] = duration
        if d.get('status') not in ['Agendado', 'Confirmado', 'Concluído', 'Cancelado']:
            raise ValueError('Status inválido.')
        if d['status'] != 'Cancelado':
            from datetime import timedelta
            end = start + timedelta(minutes=duration)
            for a in c.execute("SELECT * FROM appointments WHERE status != 'Cancelado' AND id != ?", (row_id or -1,)):
                other = datetime.fromisoformat(a['starts_at'])
                if start < other + timedelta(minutes=a['duration']) and end > other:
                    raise ValueError('Já existe um atendimento nesse horário. Escolha outro intervalo.')

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/data':
            with connect() as c:
                return self.reply(200, {t: [dict(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY id DESC')] for t in TABLES})
        files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css')}
        if path not in files:
            return self.reply(404, {'error': 'Página não encontrada.'})
        filename, mime = files[path]
        body = (ROOT / 'static' / filename).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def mutate(self, method):
        parts = urlparse(self.path).path.strip('/').split('/')
        if len(parts) not in (2, 3) or parts[0] != 'api' or parts[1] not in TABLES:
            return self.reply(404, {'error': 'Recurso não encontrado.'})
        table = parts[1]
        try:
            row_id = int(parts[2]) if len(parts) == 3 else None
            if (method == 'POST' and row_id is not None) or (method != 'POST' and row_id is None):
                raise ValueError('Operação inválida.')
            with connect() as c:
                if row_id is not None and not c.execute(f'SELECT id FROM {table} WHERE id=?', (row_id,)).fetchone():
                    return self.reply(404, {'error': 'Registro não encontrado.'})
                if method == 'DELETE':
                    c.execute(f'DELETE FROM {table} WHERE id=?', (row_id,))
                else:
                    size = int(self.headers.get('Content-Length', 0))
                    if size > 100000:
                        raise ValueError('Registro muito grande.')
                    d = json.loads(self.rfile.read(size))
                    d = {k: d[k] for k in TABLES[table] if k in d}
                    validate(table, d, c, row_id)
                    if method == 'POST':
                        cols = list(d)
                        result = c.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", list(d.values()))
                        row_id = result.lastrowid
                    else:
                        c.execute(f"UPDATE {table} SET {','.join(k+'=?' for k in d)} WHERE id=?", [*d.values(), row_id])
            self.reply(200, {'id': row_id, 'ok': True})
        except (ValueError, TypeError, sqlite3.IntegrityError) as e:
            self.reply(400, {'error': str(e) or 'Dados inválidos.'})

    def do_POST(self): self.mutate('POST')
    def do_PUT(self): self.mutate('PUT')
    def do_DELETE(self): self.mutate('DELETE')

if __name__ == '__main__':
    init()
    port = int(os.environ.get('PORT', '8000'))
    print(f'Clínica Essência disponível em http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
