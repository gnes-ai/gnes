extras_dep = {
    'bert': ['bert-serving-server>=1.8.6', 'bert-serving-client>=1.8.6'],
    # 'elmo': [
    #     'elmoformanylangs @ git+https://github.com/HIT-SCIR/ELMoForManyLangs.git@master#egg=elmoformanylangs-0.0.2',
    #     'paramiko', 'pattern3'],
    'flair': ['flair>=0.4.1'],
    'annoy': ['annoy==1.15.2'],
    'chinese': ['jieba'],
    'vision': ['opencv-python>=4.0.0', 'imagehash>=4.0'],
    'leveldb': ['plyvel>=1.0.5'],
    'test': ['pylint', 'memory_profiler>=0.55.0', 'psutil>=5.6.1', 'gputil>=1.4.0'],
    'transformers': ['pytorch-transformers'],
    'onnx': ['onnxruntime'],
    'audio': ['librosa>=0.7.0'],
    'scipy': ['scipy']
}


def combine_dep(new_key, base_keys):
    extras_dep[new_key] = list(set(k for v in base_keys for k in extras_dep[v]))


combine_dep('nlp', ['bert', 'flair', 'transformers'])
combine_dep('cn_nlp', ['chinese', 'nlp'])
combine_dep('all', [k for k in extras_dep if k != 'elmo'])

for k, v in extras_dep.items():
    print('<tr><td><pre>%s</pre></td><td>%s</td>' % ('pip install gnes[%s]' % k, ', '.join(v)))
