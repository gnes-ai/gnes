from gnes.encoder.image.vgg import VggEncoder
from gnes.preprocessor.image.simple import ImagePreprocessor
import unittest
import os


class TestVggEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'vgg_encoder.bin')

        imagePreprocessor = ImagePreprocessor()
        self.test_img = imagePreprocessor.img_process_for_test(dirname)
        self.vgg_encoder = VggEncoder('/ext_data/image_encoder')

    def test_encoding(self):
        vec = self.vgg_encoder.encode(self.test_img)
        self.assertEqual(vec.shape[0], len(self.test_img))
        self.assertEqual(vec.shape[1], 4096)

    def test_dump_load(self):
        self.vgg_encoder.dump(self.dump_path)

        vgg_encoder2 = VggEncoder.load(self.dump_path)

        vec = vgg_encoder2.encode(self.test_img)
        self.assertEqual(vec.shape[0], len(self.test_img))
        self.assertEqual(vec.shape[1], 4096)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)

