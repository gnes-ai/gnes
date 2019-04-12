from pytorch_pretrained_bert import GPT2Model, GPT2Tokenizer

from .gpt import GPTEncoder


class GPT2Encoder(GPTEncoder):
    def _get_token_ids(self, x):
        return self._tokenizer.encode(x)

    def _get_output_tensor(self, x):
        return self._model(x)[0]

    def _init_model_tokenizer(self):
        self._tokenizer = GPT2Tokenizer.from_pretrained(self.model_path)
        self._model = GPT2Model.from_pretrained(self.model_path)
        self._model.eval()
