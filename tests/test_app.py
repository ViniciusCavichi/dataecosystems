import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

spec = importlib.util.spec_from_file_location('clinic', Path(__file__).resolve().parents[1] / 'app.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class ClinicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        app.DB = Path(cls.tmp.name) / 'test.db'
        app.init()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.tmp.cleanup()

    def request(self, path, method='GET', data=None):
        req = Request(self.base + path, data=json.dumps(data).encode() if data is not None else None, method=method, headers={'Content-Type': 'application/json'})
        try:
            with urlopen(req) as r:
                return r.status, json.loads(r.read())
        except HTTPError as e:
            return e.code, json.loads(e.read())

    def test_full_clinic_workflow(self):
        c = {'name':'Ana Teste', 'age':32, 'phone':'11999990000', 'address':'Rua A, 10', 'email':'ana@example.com', 'instagram':'@ana', 'notes':'Pele sensível'}
        status, result = self.request('/api/clients', 'POST', c)
        self.assertEqual(status, 200)
        cid = result['id']
        a = {'client_id':cid, 'starts_at':'2026-10-23T09:00','duration':60,'service':'Limpeza de pele','status':'Agendado','notes':''}
        status, result = self.request('/api/appointments','POST',a)
        self.assertEqual(status,200)
        aid = result['id']
        self.assertEqual(self.request('/api/appointments','POST',{**a,'starts_at':'2026-10-23T09:30'})[0],400)
        self.assertEqual(self.request('/api/appointments','POST',{**a,'starts_at':'2026-10-23T10:00'})[0],200)
        self.assertEqual(self.request(f'/api/appointments/{aid}','PUT',{**a,'status':'Concluído'})[0],200)
        r = {'client_id':cid,'date':'2026-10-23','procedure':'Limpeza','evolution':'Boa resposta ao procedimento.','recommendations':'Usar protetor solar.'}
        status, result = self.request('/api/records','POST',r)
        self.assertEqual(status,200)
        rid=result['id']
        self.assertEqual(self.request(f'/api/records/{rid}','PUT',{**r,'evolution':'Melhora da textura.'})[0],200)
        app.init()
        stored=self.request('/api/data')[1]
        self.assertEqual(stored['clients'][0]['address'],c['address'])
        self.assertEqual(stored['records'][0]['evolution'],'Melhora da textura.')
        self.assertEqual(self.request(f'/api/records/{rid}','DELETE')[0],200)
        self.assertEqual(self.request('/api/data')[1]['records'],[])
        self.assertEqual(self.request('/api/clients','POST',{'name':''})[0],400)
        self.assertEqual(self.request('/api/records','POST',{**r,'client_id':9999})[0],400)
        self.assertEqual(self.request('/api/clients','POST',{**c,'age':150})[0],400)

    def test_static_application(self):
        for path, marker in [('/',b'Ess'),('/app.js',b'load()'),('/style.css',b'--brown')]:
            with urlopen(self.base+path) as response:
                self.assertEqual(response.status,200)
                self.assertIn(marker,response.read())

if __name__ == '__main__':
    unittest.main()
