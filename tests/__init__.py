import os

env_dict = {
    'orange-ci': {
        'BERT_CI_PORT': 7125,
        'BERT_CI_PORT_OUT': 7126,
        'BERT_CI_MODEL': '/chinese_L-12_H-768_A-12',
        'ELMO_CI_MODEL': '/zhs.model',
        'FLAIR_CI_MODEL': 'multi-forward-fast',
        'GPT_CI_MODEL': '/openai_gpt',
        'GPT2_CI_MODEL': '/openai_gpt2',
        'XL_CI_MODEL': '/transformer_xl_wt103',
        'WORD2VEC_MODEL': '/sgns.wiki.bigram-char.sample',
        'GNES_PROFILING': 1
    },
    'idc-165': {
        'BERT_CI_PORT': 7125,
        'BERT_CI_PORT_OUT': 7126,
        'BERT_CI_MODEL': '/ext_data/chinese_L-12_H-768_A-12',
        'ELMO_CI_MODEL': '/ext_data/zhs.model',
        'FLAIR_CI_MODEL': 'multi-forward-fast',
        'GPT_CI_MODEL': '/ext_data/openai_gpt',
        'GPT2_CI_MODEL': '/ext_data/openai_gpt2',
        'XL_CI_MODEL': '/ext_data/transformer_xl_wt103',
        'WORD2VEC_MODEL': '/ext_data/sgns.wiki.bigram-char.sample',
        'GNES_PROFILING': 1
    }

}

for k, v in env_dict[os.environ.get('GNES_ENV_SET', 'idc-165')].items():
    if k not in os.environ:
        os.environ[k] = str(v)
    else:
        print('os.environ["%s"]=%s exists already, i wont setting it to %s' % (k, os.environ[k], str(v)))
