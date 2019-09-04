#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from .base import YamlComposer, parse_http_data
from ..cli.parser import set_composer_parser
from ..helper import set_logger


class YamlComposerHttp:
    def __init__(self, args):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)

    class _HttpServer(BaseHTTPRequestHandler):
        args = set_composer_parser().parse_args([])
        default_html = YamlComposer(args).build_all()['html']

        def _set_response(self, msg: str, code: int = 200):
            self.send_response(code)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(msg.encode('utf-8'))

        def do_GET(self):
            if str(self.path) != '/':
                self._set_response('<h1>"%s" is not a valid entrypoint</h1>' % self.path, 400)
                return
            self._set_response(self.default_html)

        def do_POST(self):
            if str(self.path) != '/generate':
                self._set_response('<h1>"%s" is not a valid entrypoint</h1>' % self.path, 400)
                return
            content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
            data = self.rfile.read(content_length)  # <--- Gets the data itself

            data = {k: v[0] for k, v in parse_qs(data.decode('utf-8')).items()}
            self._set_response(*parse_http_data(data, self.args))

    def run(self):
        httpd = HTTPServer(('0.0.0.0', self.args.http_port), self._HttpServer)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
