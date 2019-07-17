from .base import BaseImagePreprocessor
from ...proto import array2blob
from PIL import Image
import numpy as np
import io
import os


class SegmentPreprocessor(BaseImagePreprocessor):

    def __init__(self, model_name: str,
                 model_dir: str,
                 target_img_size: int = 224,
                 _use_cuda: bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.model_dir = model_dir
        self.target_img_size = target_img_size
        self.model_name = model_name
        self._use_cuda = _use_cuda

    def post_init(self):
        import torch
        import torchvision.models as models

        os.environ['TORCH_HOME'] = self.model_dir
        self._model = getattr(models.detection, self.model_name)(pretrained=True)
        self._model = self._model.eval()
        if self._use_cuda:
            # self._model.cuda()
            self._device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            self._model = self._model.to(self._device)

    def apply(self, doc: 'gnes_pb2.Document'):
        super().apply(doc)
        if doc.raw_bytes:
            original_image = Image.open(io.BytesIO(doc.raw_bytes))
            image_tensor = self._torch_transform(original_image)

            seg_output = self._model([image_tensor])
            chunks = seg_output[0]['boxes'].tolist()
            weight = seg_output[0]['scores'].tolist()
            for ci, ele in enumerate(zip(chunks, weight)):
                c = doc.chunks.add()
                c.doc_id = doc.doc_id
                c.blob.CopyFrom(array2blob(self._crop_image_reshape(original_image, ele[0])))
                c.offset_1d = ci
                c.weight = ele[1]
        else:
            self.logger.error('bad document: "raw_bytes" is empty!')

    def _crop_image_reshape(self, original_image, coordinates):
        return np.array(original_image.crop(coordinates).resize((self.target_img_size,
                                                                 self.target_img_size)))
