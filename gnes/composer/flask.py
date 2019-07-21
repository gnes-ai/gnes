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

import tempfile

from .base import YamlComposer
from ..cli.parser import set_composer_parser
from ..helper import set_logger


class YamlComposerFlask:
    def __init__(self, args):
        self.args = args
        self.logger = set_logger(self.__class__.__name__, self.args.verbose)

    def _create_flask_app(self):
        try:
            from flask import Flask, request
            from flask_compress import Compress
            from flask_cors import CORS
        except ImportError:
            raise ImportError('Flask or its dependencies are not fully installed, '
                              'they are required for serving HTTP requests.'
                              'Please use "pip install gnes[http]" to install it.')

        # support up to 10 concurrent HTTP requests
        app = Flask(__name__)

        @app.route('/', methods=['GET'])
        def _get_homepage():
            return YamlComposer(set_composer_parser().parse_args([])).build_all()['html']

        @app.route('/generate', methods=['POST'])
        def _regenerate():
            data = request.form if request.form else request.json
            if not data or 'yaml-config' not in data:
                return '<h1>Bad POST request</h1> your POST request does not contain "yaml-config" field!', 406
            f = tempfile.NamedTemporaryFile('w', delete=False).name
            with open(f, 'w', encoding='utf8') as fp:
                fp.write(data['yaml-config'])
            try:
                return YamlComposer(set_composer_parser().parse_args([
                    '--yaml_path', f
                ])).build_all()['html']
            except Exception as e:
                self.logger.error(e)
                return '<h1>Bad YAML input</h1> please kindly check the format, indent and content of your YAML file!', 400

        CORS(app, origins=self.args.cors)
        Compress().init_app(app)
        return app

    def run(self):
        app = self._create_flask_app()
        app.run(port=self.args.http_port, threaded=True, host='0.0.0.0')
