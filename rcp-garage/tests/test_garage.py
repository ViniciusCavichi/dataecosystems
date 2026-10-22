import importlib.util,json,tempfile,threading,unittest,subprocess,shutil
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
spec=importlib.util.spec_from_file_location('garage',Path(__file__).resolve().parents[1]/'app.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
class GarageTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();app.DB=Path(self.tmp.name)/'garage.db';app.init();self.server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.base=f'http://127.0.0.1:{self.server.server_port}'
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
 def request(self,path,method='GET',data=None):
  req=Request(self.base+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
  try:
   with urlopen(req) as r:return r.status,json.loads(r.read())
  except HTTPError as e:return e.code,json.loads(e.read())
 def create(self,table,data):
  code,result=self.request('/api/'+table,'POST',data);self.assertEqual(code,200,result);return result['id']
 def test_workflow_and_pdf(self):
  cid=self.create('clients',{'name':'João da Silva','address':'Rua São José, 25','email':'joao@example.com','phone':'11999999999','age':40})
  vid=self.create('vehicles',{'client_id':cid,'name':'Triciclo RCP 1600','plate':'ABC1D23','year':'2020','chassis':'123XYZ','color':'Vermelho'})
  task={'title':'Entregar triciclo revisado','client_id':cid,'vehicle_id':vid,'date':'2026-10-25','time':'14:00','status':'A fazer','priority':'Entrega','notes':'Conferir freios\nTestar iluminação'}
  tid=self.create('tasks',task)
  self.assertEqual(self.request(f'/api/tasks/{tid}','PUT',{**task,'status':'Concluída'})[0],200)
  q={'client_id':cid,'vehicle_id':vid,'date':'2026-10-22','valid_until':'2026-11-22','status':'Rascunho','items':[{'description':'Revisão dos freios','quantity':'2','price':'150.25'},{'description':'Peça especial','quantity':'1.5','price':'10.10'}],'notes':'Pagamento na entrega.'}
  qid=self.create('quotes',q)
  state=self.request('/api/data')[1];quote=state['quotes'][0]
  self.assertEqual(sum(i['total_cents'] for i in quote['items']),31565)
  self.assertEqual(self.request('/api/settings','PUT',{'name':'RCP Garage','document':'00.000.000/0001-00','address':'Rua da Oficina, 10','phone':'1133334444','email':'rcp@example.com','logo':''})[0],200)
  with urlopen(self.base+f'/api/pdf/{qid}') as response:
   pdf=response.read();self.assertEqual(response.headers.get_content_type(),'application/pdf');self.assertIn('attachment',response.headers['Content-Disposition']);self.assertTrue(pdf.startswith(b'%PDF-1.4'))
  path=Path(self.tmp.name)/'quote.pdf';path.write_bytes(pdf)
  if shutil.which('pdftotext'):
   result=subprocess.run(['pdftotext',str(path),'-'],capture_output=True,text=True,check=True)
   for text in ['RCP Garage','João da Silva','Triciclo RCP 1600','Revisão dos freios','315,65','00.000.000/0001-00']:self.assertIn(text,result.stdout)
  app.init();self.assertEqual(self.request('/api/data')[1]['tasks'][0]['status'],'Concluída')
  self.assertEqual(self.request(f'/api/clients/{cid}','DELETE')[0],400)
  cid2=self.create('clients',{'name':'Outro proprietário'})
  self.assertEqual(self.request('/api/quotes','POST',{**q,'client_id':cid2})[0],400)
  self.assertEqual(self.request(f'/api/vehicles/{vid}','PUT',{'client_id':cid2,'name':'Triciclo'})[0],400)
  self.assertEqual(self.request('/api/quotes','POST',{**q,'items':[{'description':'Inválido','quantity':0,'price':1}]})[0],400)
  self.assertEqual(self.request('/api/quotes','POST',{**q,'items':[{'description':'Inválido','quantity':1,'price':-1}]})[0],400)
  self.assertEqual(self.request('/api/quotes','POST',{**q,'valid_until':'2026-01-01'})[0],400)
  self.assertEqual(self.request(f'/api/quotes/{qid}','PUT',{**q,'status':'Aprovado'})[0],200)
  self.assertEqual(self.request(f'/api/tasks/{tid}','DELETE')[0],200)
 def test_multipage_pdf(self):
  cid=self.create('clients',{'name':'Cliente de teste'})
  qid=self.create('quotes',{'client_id':cid,'date':'2026-10-22','status':'Enviado','items':[{'description':f'Serviço {n}: manutenção e fabricação de componentes especiais com revisão detalhada','quantity':1,'price':'10.00'} for n in range(100)]})
  with urlopen(self.base+f'/api/pdf/{qid}') as r:pdf=r.read()
  self.assertGreater(pdf.count(b'/Type /Page '),1)
  path=Path(self.tmp.name)/'long.pdf';path.write_bytes(pdf)
  if shutil.which('pdftotext'):
   text=subprocess.run(['pdftotext',str(path),'-'],capture_output=True,text=True,check=True).stdout
   self.assertIn('Serviço 99',text);self.assertIn('1.000,00',text)
 def test_static_and_missing_pdf(self):
  for path in ['/','/style.css','/app.js','/logo.svg']:
   with urlopen(self.base+path) as r:self.assertEqual(r.status,200);self.assertGreater(len(r.read()),50)
  self.assertEqual(self.request('/api/pdf/999')[0],404)
  self.assertEqual(self.request('/api/clients','POST',{'name':''})[0],400)
  self.assertEqual(self.request('/api/settings','PUT',{'name':'RCP','logo':'data:image/svg+xml;base64,invalid'})[0],400)
if __name__=='__main__':unittest.main()
