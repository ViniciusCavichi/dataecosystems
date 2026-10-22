"""Inicia a RCP Garage e abre o navegador no Windows."""
import runpy
import threading
import urllib.request
import webbrowser
import time
import os
from pathlib import Path


def open_when_ready():
    url = 'http://127.0.0.1:' + os.environ.get('PORT', '8001')
    for _ in range(40):
        try:
            with urllib.request.urlopen(url + '/api/data', timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except OSError:
            time.sleep(0.25)


if __name__ == '__main__':
    print('Mantenha esta janela aberta enquanto usa a RCP Garage.')
    print('Para encerrar, pressione Ctrl+C ou feche esta janela.')
    threading.Thread(target=open_when_ready, daemon=True).start()
    try:
        runpy.run_path(str(Path(__file__).with_name('app.py')), run_name='__main__')
    except KeyboardInterrupt:
        print('Aplicacao encerrada.')
