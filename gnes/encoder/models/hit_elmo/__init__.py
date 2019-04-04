import os
import json

import torch

from ..base_torch import BaseTorchModel

from .embedding_layer import EmbeddingLayer
from .token_embedder import ConvTokenEmbedder, LstmTokenEmbedder
from .elmo import ElmobiLm
from .lstm import LstmbiLm


class HitElmo(BaseTorchModel):
    """ Pre-trained ELMo Representations for Many Languages implemented by HIT.

    codes are borrowed from: https://github.com/HIT-SCIR/ELMoForManyLangs
    """
    def __init__(self, model_dir, config_path=None, use_cuda=None, *args, **kwargs):
        super().__init__(model_dir, use_cuda, *args, **kwargs)

        config_path = config_path if config_path else os.path.join(
            self.model_dir, 'config.json')

        with open(config_path, 'r') as f:
            config = json.load(f)

        # For the model trained with character-based word encoder.
        if config['token_embedder']['char_dim'] > 0:
            self.char_lexicon = {}
            with open(os.path.join(self.model_dir, 'char.dict'), 'r') as f:
                for line in f:
                    tokens = line.strip().split('\t')
                    if len(tokens) == 1:
                        tokens.insert(0, '\u3000')
                    token, i = tokens
                    self.char_lexicon[token] = int(i)

            char_emb_layer = EmbeddingLayer(
                self.config['token_embedder']['char_dim'], self.char_lexicon, fix_emb=False, embs=None, logger=self.logger)
            self.logger.info('char embedding size: ' +
                             str(len(char_emb_layer.word2id)))
        else:
            self.char_lexicon = None
            char_emb_layer = None

        # For the model trained with word form word encoder.
        if config['token_embedder']['word_dim'] > 0:
            self.word_lexicon = {}
            with open(os.path.join(self.model_dir, 'word.dict'), 'r') as f:
                for line in f:
                    tokens = line.strip().split('\t')
                    if len(tokens) == 1:
                        tokens.insert(0, '\u3000')
                    token, i = tokens
                    self.word_lexicon[token] = int(i)

            word_emb_layer = EmbeddingLayer(
                config['token_embedder']['word_dim'], self.word_lexicon, fix_emb=False, embs=None, logger=self.logger)
            self.logger.info('word embedding size: ' +
                             str(len(word_emb_layer.word2id)))
        else:
            self.word_lexicon = None
            word_emb_layer = None

        if config['token_embedder']['name'].lower() == 'cnn':
            self.token_embedder = ConvTokenEmbedder(
                config, word_emb_layer, char_emb_layer, self.use_cuda)
        elif config['token_embedder']['name'].lower() == 'lstm':
            self.token_embedder = LstmTokenEmbedder(
                config, word_emb_layer, char_emb_layer, self.use_cuda)

        if config['encoder']['name'].lower() == 'elmo':
            self.encoder = ElmobiLm(config, self.use_cuda)
        elif config['encoder']['name'].lower() == 'lstm':
            self.encoder = LstmbiLm(config, self.use_cuda)

        self.output_dim = config['encoder']['projection_dim']

        if self.use_cuda:
            self.cuda()

        self.load_model(self.model_dir)


    def load_model(self, path):
        self.token_embedder.load_state_dict(torch.load(os.path.join(path, 'token_embedder.pkl'),
                                                       map_location=lambda storage, loc: storage))
        self.encoder.load_state_dict(torch.load(os.path.join(path, 'encoder.pkl'),
                                                map_location=lambda storage, loc: storage))
