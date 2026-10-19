"""FluidLab: servidor local de física de fluidos (sin dependencias externas)."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path

from physics import calculate, PhysicsError

ROOT=Path(__file__).resolve().parent
WEB=ROOT/'web'
ROUTES={'/':WEB/'index.html', '/index.html':WEB/'index.html',
        '/styles.css':WEB/'styles.css','/app.js':WEB/'app.js'}

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, content, ctype):
        self.send_response(code)
        self.send_header('Content-Type',ctype)
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _json(self, code, obj):
        data=json.dumps(obj,ensure_ascii=False,allow_nan=False).encode('utf-8')
        self._send(code,data,'application/json; charset=utf-8')

    def do_GET(self):
        path=self.path.split('?',1)[0]
        if path == '/api/health':
            return self._json(200,{'ok':True,'engine':'Python stdlib','application':'FluidLab'})
        target=ROUTES.get(path)
        if target is None or not target.is_file():
            return self._json(404,{'error':'Ruta no encontrada'})
        ctype=(mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        if ctype.startswith('text/') or ctype=='application/javascript':
            ctype+='; charset=utf-8'
        self._send(200,target.read_bytes(),ctype)

    def do_POST(self):
        if self.path != '/api/calculate':
            return self._json(404,{'error':'Ruta no encontrada'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<2 or length>32_768:
                return self._json(413,{'error':'Solicitud vacía o demasiado grande (máx. 32 KB).'})
            req=json.loads(self.rfile.read(length).decode('utf-8'))
            return self._json(200,calculate(req))
        except (PhysicsError,ValueError,json.JSONDecodeError,UnicodeDecodeError) as exc:
            return self._json(400,{'error':str(exc)})
        except (OverflowError,ZeroDivisionError):
            return self._json(400,{'error':'Parámetros demasiado extremos para el cálculo.'})

    def log_message(self, format, *args):
        if not self.path.startswith('/api/calculate'):
            super().log_message(format,*args)


def main():
    parser=argparse.ArgumentParser(description='FluidLab — Mecánica de fluidos')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--host',default='127.0.0.1',help='Por seguridad se inicia solo en localhost.')
    args=parser.parse_args()
    with ThreadingHTTPServer((args.host,args.port), Handler) as server:
        print(f'FluidLab ejecutándose en http://{args.host}:{args.port}')
        print('Abre la URL en tu navegador. Presiona Ctrl+C para salir.')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido.')

if __name__ == '__main__':
    main()
