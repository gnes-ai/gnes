from typing import List, Any, Dict

import os
import json

import torch
from torch.autograd import Variable

import numpy as np

from ..base_torch import BaseTorchModel

from .embedding_layer import EmbeddingLayer
from .token_embedder import ConvTokenEmbedder, LstmTokenEmbedder
from .elmo import ElmobiLm
from .lstm import LstmbiLm
from .data_utils import preprocess_data, create_batches, recover


class HitElmo(BaseTorchModel):
    """ Pre-trained ELMo Representations for Many Languages implemented by HIT.

    codes are borrowed from: https://github.com/HIT-SCIR/ELMoForManyLangs
    """

    def __init__(self, model_dir, config_path, use_cuda=None, *args, **kwargs):
        super().__init__(use_cuda=use_cuda, *args, **kwargs)

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.batch_size = kwargs.get('batch_size', 500)


        self.model_dir = model_dir

        # initializse model instance
        self.get_model()

        # load model from checkout point
        self.load_model(self.model_dir)

    def forward(self, word_inp, chars_package, mask_package):
        """
        :param word_inp:
        :param chars_package:
        :param mask_package:
        :return:
        """
        token_embedding = self.token_embedder(
            word_inp, chars_package,
            (mask_package[0].size(0), mask_package[0].size(1)))
        if self.config['encoder']['name'] == 'elmo':
            mask = Variable(
                mask_package[0]).cuda() if self.use_cuda else Variable(
                    mask_package[0])
            encoder_output = self.encoder(token_embedding, mask)
            sz = encoder_output.size()
            token_embedding = torch.cat([token_embedding, token_embedding],
                                        dim=2).view(1, sz[1], sz[2], sz[3])
            encoder_output = torch.cat([token_embedding, encoder_output],
                                       dim=0)
        elif self.config['encoder']['name'] == 'lstm':
            encoder_output = self.encoder(token_embedding)
        else:
            raise ValueError('Unknown encoder: {0}'.format(
                self.config['encoder']['name']))

        return encoder_output

    def predict(self, x: List[str], *args, **kwargs) -> np.ndarray:
        output_layer = kwargs.get('output_layer', -1)

        if self.config['token_embedder']['name'].lower() == 'cnn':
            input_data, text = preprocess_data(
                x, self.config['token_embedder']['max_characters_per_token'])
        else:
            input_data, text = preprocess_data(x)

        # create test batches from the input data.
        test_w, test_c, test_lens, test_masks, test_text, recover_ind = create_batches(
            input_data,
            self.batch_size,
            self.word_lexicon,
            self.char_lexicon,
            self.config,
            text=text)

        cnt = 0

        after_elmo = []
        for w, c, lens, masks, texts in zip(test_w, test_c, test_lens,
                                            test_masks, test_text):
            output = self.forward(w, c, masks)
            for i, text in enumerate(texts):
                if self.config['encoder']['name'].lower() == 'lstm':
                    data = output[i, 1:lens[i] - 1, :].data
                    if self.use_cuda:
                        data = data.cpu()
                    data = data.numpy()
                elif self.config['encoder']['name'].lower() == 'elmo':
                    data = output[:, i, 1:lens[i] - 1, :].data
                    if self.use_cuda:
                        data = data.cpu()
                    data = data.numpy()

                if output_layer == -1:
                    payload = np.average(data, axis=0)
                elif output_layer == -2:
                    payload = data
                else:
                    payload = data[output_layer]
                after_elmo.append(payload)

                cnt += 1
                if cnt % 1000 == 0:
                    self.logger.info('Finished {0} sentences.'.format(cnt))

        after_elmo = recover(after_elmo, recover_ind)

        return after_elmo

    def get_model(self):
        # For the model trained with character-based word encoder.
        if self.config['token_embedder']['char_dim'] > 0:
            self.char_lexicon = {}
            with open(os.path.join(self.model_dir, 'char.dic'), 'r') as f:
                for line in f:
                    tokens = line.strip().split('\t')
                    if len(tokens) == 1:
                        tokens.insert(0, '\u3000')
                    token, i = tokens
                    self.char_lexicon[token] = int(i)

            char_emb_layer = EmbeddingLayer(
                self.config['token_embedder']['char_dim'],
                self.char_lexicon,
                fix_emb=False,
                embs=None,
                logger=self.logger)
            self.logger.info('char embedding size: ' +
                             str(len(char_emb_layer.word2id)))
        else:
            self.char_lexicon = None
            char_emb_layer = None

        # For the model trained with word form word encoder.
        if self.config['token_embedder']['word_dim'] > 0:
            self.word_lexicon = {}
            with open(os.path.join(self.model_dir, 'word.dic'), 'r') as f:
                for line in f:
                    tokens = line.strip().split('\t')
                    if len(tokens) == 1:
                        tokens.insert(0, '\u3000')
                    token, i = tokens
                    self.word_lexicon[token] = int(i)

            word_emb_layer = EmbeddingLayer(
                self.config['token_embedder']['word_dim'],
                self.word_lexicon,
                fix_emb=False,
                embs=None,
                logger=self.logger)
            self.logger.info('word embedding size: ' +
                             str(len(word_emb_layer.word2id)))
        else:
            self.word_lexicon = None
            word_emb_layer = None

        if self.config['token_embedder']['name'].lower() == 'cnn':
            self.token_embedder = ConvTokenEmbedder(
                self.config, word_emb_layer, char_emb_layer, self.use_cuda)
        elif self.config['token_embedder']['name'].lower() == 'lstm':
            self.token_embedder = LstmTokenEmbedder(
                self.config, word_emb_layer, char_emb_layer, self.use_cuda)

        if self.config['encoder']['name'].lower() == 'elmo':
            self.encoder = ElmobiLm(self.config, self.use_cuda)
        elif self.config['encoder']['name'].lower() == 'lstm':
            self.encoder = LstmbiLm(self.config, self.use_cuda)

        self.output_dim = self.config['encoder']['projection_dim']

        if self.use_cuda:
            self.cuda()

    def load_model(self, path):
        self.token_embedder.load_state_dict(
            torch.load(
                os.path.join(path, 'token_embedder.pkl'),
                map_location=lambda storage, loc: storage))
        self.encoder.load_state_dict(
            torch.load(
                os.path.join(path, 'encoder.pkl'),
                map_location=lambda storage, loc: storage))
