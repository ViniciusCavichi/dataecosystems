"""RCP Garage: servidor local, SQLite e PDF sem dependencias externas."""
import json, os, sqlite3, base64
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('RCP_DB',str(ROOT/'data'/'garage.db')))
FIELDS={'clients':['name','address','age','email','phone','instagram','notes'],'vehicles':['client_id','name','plate','year','chassis','color','notes'],'tasks':['client_id','vehicle_id','title','date','time','status','priority','notes'],'quotes':['client_id','vehicle_id','date','valid_until','status','items','notes']}
def db():
 DB.parent.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
def init():
 with db() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY,name TEXT NOT NULL,address TEXT DEFAULT '',age INTEGER,email TEXT DEFAULT '',phone TEXT DEFAULT '',instagram TEXT DEFAULT '',notes TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS vehicles(id INTEGER PRIMARY KEY,client_id INTEGER NOT NULL REFERENCES clients(id),name TEXT NOT NULL,plate TEXT DEFAULT '',year TEXT DEFAULT '',chassis TEXT DEFAULT '',color TEXT DEFAULT '',notes TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,client_id INTEGER REFERENCES clients(id),vehicle_id INTEGER REFERENCES vehicles(id),title TEXT NOT NULL,date TEXT NOT NULL,time TEXT DEFAULT '',status TEXT NOT NULL,priority TEXT NOT NULL,notes TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS quotes(id INTEGER PRIMARY KEY,client_id INTEGER NOT NULL REFERENCES clients(id),vehicle_id INTEGER REFERENCES vehicles(id),date TEXT NOT NULL,valid_until TEXT DEFAULT '',status TEXT NOT NULL,items TEXT NOT NULL,notes TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),value TEXT NOT NULL);''')
  c.execute('INSERT OR IGNORE INTO settings VALUES(1,?)',(json.dumps({'name':'RCP Garage','document':'','address':'','phone':'','email':'','logo':''}),))
def money_cents(value):
 try:
  d=Decimal(str(value))
  if not d.is_finite() or d<0 or d>Decimal('100000000'):raise ValueError('Valor fora do limite.')
  return int((d*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
 except InvalidOperation:raise ValueError('Valor inválido.')
def currency(cents):return ('R$ '+f'{cents/100:,.2f}').replace(',','X').replace('.',',').replace('X','.')
def validate(t,d,c):
 for k in d:
  if isinstance(d[k],str):d[k]=d[k].strip()
 for f in {'clients':['name'],'vehicles':['name','client_id'],'tasks':['title','date','status','priority'],'quotes':['client_id','date','status','items']}[t]:
  if not d.get(f):raise ValueError('Preencha os campos obrigatórios.')
 if t=='clients':
  d['age']=None if d.get('age') in ('',None) else int(d['age'])
  if d['age'] is not None and not 0<=d['age']<=120:raise ValueError('Idade inválida.')
 for key,table in [('client_id','clients'),('vehicle_id','vehicles')]:
  if key in d:
   d[key]=int(d[key]) if d[key] else None
   if d[key] and not c.execute(f'SELECT id FROM {table} WHERE id=?',(d[key],)).fetchone():raise ValueError('Cliente ou veículo não encontrado.')
 if d.get('vehicle_id'):
  v=c.execute('SELECT client_id FROM vehicles WHERE id=?',(d['vehicle_id'],)).fetchone()
  if v['client_id']!=d.get('client_id'):raise ValueError('O veículo deve pertencer ao cliente selecionado.')
 for f in ['date','valid_until']:
  if d.get(f):datetime.strptime(d[f],'%Y-%m-%d')
 if t=='tasks':
  if d.get('time'):datetime.strptime(d['time'],'%H:%M')
  if d['status'] not in ['A fazer','Em andamento','Concluída','Cancelada'] or d['priority'] not in ['Normal','Alta','Entrega']:raise ValueError('Status ou prioridade inválidos.')
 if t=='vehicles' and d.get('year'):
  if not d['year'].isdigit() or not 1900<=int(d['year'])<=date.today().year+2:raise ValueError('Ano inválido.')
 if t=='quotes':
  if d['status'] not in ['Rascunho','Enviado','Aprovado','Recusado']:raise ValueError('Status inválido.')
  if d.get('valid_until') and d['valid_until']<d['date']:raise ValueError('Validade anterior à emissão.')
  items=d['items']
  if not isinstance(items,list) or not 1<=len(items)<=200:raise ValueError('Inclua de 1 a 200 itens.')
  cleaned=[]
  for item in items:
   desc=str(item.get('description','')).strip()
   qty=Decimal(str(item.get('quantity',0)))
   if not desc or not qty.is_finite() or qty<=0 or qty>100000:raise ValueError('Descrição e quantidade positiva são obrigatórias.')
   cents=money_cents(item.get('price',0))
   cleaned.append({'description':desc,'quantity':str(qty),'price_cents':cents,'total_cents':int((qty*cents).quantize(Decimal('1'),rounding=ROUND_HALF_UP))})
  d['items']=json.dumps(cleaned,ensure_ascii=False)
def make_pdf(q,client,vehicle,s):
 import textwrap
 lines=[]
 def add(text='',size=10):
  for line in str(text).splitlines() or ['']:
   for part in textwrap.wrap(line,90 if size<=10 else 55,replace_whitespace=False) or ['']:lines.append((part,size))
 add(s.get('name') or 'RCP Garage',22);add('FABRICAÇÃO E MANUTENÇÃO DE TRICICLOS',10)
 for key,label in [('document','CNPJ/CPF'),('address','Endereço'),('phone','Telefone'),('email','E-mail')]:
  if s.get(key):add(label+': '+s[key])
 add();add(f"ORÇAMENTO #{q['id']:05d}",16)
 add('Emissão: '+q['date']+'   Validade: '+(q['valid_until'] or 'Não informada'))
 add('Situação: '+q['status']);add();add('CLIENTE',13)
 for key,label in [('name','Nome'),('document','Documento'),('address','Endereço'),('phone','Telefone'),('email','E-mail'),('instagram','Instagram')]:
  if client.get(key):add(label+': '+str(client[key]))
 if vehicle:
  add();add('VEÍCULO',13)
  for key,label in [('name','Modelo / identificação'),('plate','Placa'),('year','Ano'),('chassis','Chassi'),('color','Cor')]:
   if vehicle.get(key):add(label+': '+str(vehicle[key]))
 add();add('SERVIÇOS E PEÇAS',13);total=0
 for i,item in enumerate(q['items'],1):
  add(f"{i}. {item['description']}")
  add(f"Quantidade: {item['quantity']}  |  Unitário: {currency(item['price_cents'])}  |  Subtotal: {currency(item['total_cents'])}")
  total+=item['total_cents'];add()
 add('TOTAL: '+currency(total),16)
 if q.get('notes'):add();add('CONDIÇÕES E OBSERVAÇÕES',13);add(q['notes'])
 add();add('Aprovação do cliente: ____________________________________')
 # Native multipage PDF with standard Windows-1252 Helvetica font.
 pages=[];current=[];height=0
 for line,size in lines:
  if height+size+8>690:pages.append(current);current=[];height=0
  current.append((line,size));height+=size+8
 if current:pages.append(current)
 objects=[b'',b'',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']
 page_ids=[]
 for n,page in enumerate(pages,1):
  pid=len(objects)+1;page_ids.append(pid);sid=pid+1
  commands=['0.75 0.03 0.06 rg 45 795 505 5 re f','0.08 0.08 0.08 rg'];y=770
  for line,size in page:
   safe=line.encode('cp1252','replace').decode('latin1').replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
   commands.append(f'BT /F1 {size} Tf 45 {y} Td ({safe}) Tj ET');y-=size+8
  commands.append(f'BT /F1 9 Tf 45 30 Td (RCP Garage - Pagina {n}/{len(pages)}) Tj ET')
  stream='\n'.join(commands).encode('latin1')
  objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {sid} 0 R >>'.encode())
  objects.append(f'<< /Length {len(stream)} >>\nstream\n'.encode()+stream+b'\nendstream')
 objects[0]=b'<< /Type /Catalog /Pages 2 0 R >>';objects[1]=f"<< /Type /Pages /Count {len(pages)} /Kids [{' '.join(str(i)+' 0 R' for i in page_ids)}] >>".encode()
 out=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[0]
 for i,obj in enumerate(objects,1):offsets.append(len(out));out.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
 offset=len(out);out.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
 for value in offsets[1:]:out.extend(f'{value:010d} 00000 n \n'.encode())
 out.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{offset}\n%%EOF'.encode());return bytes(out)
class Handler(BaseHTTPRequestHandler):
 def send(self,code,body,mime='application/json; charset=utf-8',filename=None):
  if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode()
  self.send_response(code);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
  if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
  self.end_headers();self.wfile.write(body)
 def do_GET(self):
  path=urlparse(self.path).path
  with db() as c:
   if path=='/api/data':
    d={t:[dict(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY id DESC')] for t in FIELDS}
    for q in d['quotes']:q['items']=json.loads(q['items'])
    d['settings']=json.loads(c.execute('SELECT value FROM settings WHERE id=1').fetchone()[0]);return self.send(200,d)
   if path.startswith('/api/pdf/'):
    try:
     row=c.execute('SELECT * FROM quotes WHERE id=?',(int(path.split('/')[-1]),)).fetchone()
     if not row:return self.send(404,{'error':'Orçamento não encontrado.'})
     q=dict(row);q['items']=json.loads(q['items']);cl=dict(c.execute('SELECT * FROM clients WHERE id=?',(q['client_id'],)).fetchone());v=c.execute('SELECT * FROM vehicles WHERE id=?',(q['vehicle_id'],)).fetchone();s=json.loads(c.execute('SELECT value FROM settings WHERE id=1').fetchone()[0])
     return self.send(200,make_pdf(q,cl,dict(v) if v else None,s),'application/pdf',f'RCP-Orcamento-{q["id"]:05d}.pdf')
    except ValueError:return self.send(400,{'error':'Número inválido.'})
  files={'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css'),'/logo.svg':('logo.svg','image/svg+xml')}
  if path not in files:return self.send(404,{'error':'Não encontrado.'})
  f,m=files[path];self.send(200,(ROOT/'static'/f).read_bytes(),m+'; charset=utf-8')
 def mutate(self,method):
  # Reject browser requests from other origins; this is a local app, not a public server.
  origin=self.headers.get('Origin')
  if origin and origin!='http://'+self.headers.get('Host',''):return self.send(403,{'error':'Origem não permitida.'})
  parts=urlparse(self.path).path.strip('/').split('/')
  try:
   if len(parts) not in (2,3) or parts[0]!='api':return self.send(404,{'error':'Não encontrado.'})
   t=parts[1]
   if t not in FIELDS and t!='settings':return self.send(404,{'error':'Não encontrado.'})
   size=int(self.headers.get('Content-Length',0))
   if size>4000000:raise ValueError('Arquivo ou dados muito grandes (máximo 4 MB).')
   d=json.loads(self.rfile.read(size)) if method!='DELETE' else {}
   with db() as c:
    if t=='settings':
     if method!='PUT':raise ValueError('Operação inválida.')
     d={k:str(d.get(k,'')) for k in ['name','document','address','phone','email','logo']}
     if not d['name'].strip():raise ValueError('Informe o nome da oficina.')
     if d['logo']:
      if not any(d['logo'].startswith('data:image/'+x+';base64,') for x in ['png','jpeg','webp']):raise ValueError('Use uma imagem PNG, JPEG ou WebP.')
      base64.b64decode(d['logo'].split(',',1)[1],validate=True)
     c.execute('UPDATE settings SET value=? WHERE id=1',(json.dumps(d),));return self.send(200,{'ok':True})
    rid=int(parts[2]) if len(parts)==3 else None
    if (method=='POST' and rid is not None) or (method!='POST' and rid is None):raise ValueError('Operação inválida.')
    if rid is not None and not c.execute(f'SELECT id FROM {t} WHERE id=?',(rid,)).fetchone():return self.send(404,{'error':'Registro não encontrado.'})
    if method=='DELETE':c.execute(f'DELETE FROM {t} WHERE id=?',(rid,))
    else:
     d={k:d[k] for k in FIELDS[t] if k in d};validate(t,d,c)
     if t=='vehicles' and rid:
      old=c.execute('SELECT client_id FROM vehicles WHERE id=?',(rid,)).fetchone()[0]
      if old!=d['client_id'] and any(c.execute(f'SELECT id FROM {table} WHERE vehicle_id=? LIMIT 1',(rid,)).fetchone() for table in ['tasks','quotes']):raise ValueError('Veículo com histórico: mantenha o proprietário para preservar os vínculos.')
     if method=='POST':rid=c.execute(f"INSERT INTO {t} ({','.join(d)}) VALUES ({','.join('?' for _ in d)})",list(d.values())).lastrowid
     else:c.execute(f"UPDATE {t} SET {','.join(k+'=?' for k in d)} WHERE id=?",[*d.values(),rid])
   self.send(200,{'ok':True,'id':rid})
  except sqlite3.IntegrityError:self.send(400,{'error':'Este registro possui vínculos. Remova os vínculos antes de excluir.'})
  except (ValueError,TypeError,KeyError,InvalidOperation) as e:self.send(400,{'error':str(e) or 'Dados inválidos.'})
 def do_POST(self):self.mutate('POST')
 def do_PUT(self):self.mutate('PUT')
 def do_DELETE(self):self.mutate('DELETE')
if __name__=='__main__':
 init();port=int(os.environ.get('PORT','8001'));server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
 print(f'RCP Garage: http://127.0.0.1:{port}',flush=True);server.serve_forever()
