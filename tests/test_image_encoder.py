import os
import unittest
import zipfile

import numpy as np
from PIL import Image

from gnes.encoder.image.base import BasePytorchEncoder


def img_process_for_test(dirname):
    zipfile_ = zipfile.ZipFile(os.path.join(dirname, 'imgs/test.zip'))
    test_img = []
    for img_file in zipfile_.namelist():
        image = Image.open(zipfile_.open(img_file, 'r'))
        img = np.array(image)
        img.resize([224, 224, 3])
        test_img.append(img)
    return test_img


class TestVggEncoder(unittest.TestCase):

    def setUp(self):
        dirname = os.path.dirname(__file__)
        self.dump_path = os.path.join(dirname, 'model.bin')
        self.test_img = img_process_for_test(dirname)
        self.vgg_yaml = os.path.join(dirname, 'yaml', 'vgg-encoder.yml')
        self.res_yaml = os.path.join(dirname, 'yaml', 'resnet-encoder.yml')
        self.inception_yaml = os.path.join(dirname, 'yaml', 'inception-encoder.yml')

    def test_vgg_encoding(self):
        self.encoder = BasePytorchEncoder.load_yaml(self.vgg_yaml)
        vec = self.encoder.encode(self.test_img)
        self.assertEqual(vec.shape[0], len(self.test_img))
        self.assertEqual(vec.shape[1], 4096)

    def test_resnet_encoding(self):
        self.encoder = BasePytorchEncoder.load_yaml(self.res_yaml)
        vec = self.encoder.encode(self.test_img)
        self.assertEqual(vec.shape[0], len(self.test_img))
        self.assertEqual(vec.shape[1], 2048)

    def test_inception_encoding(self):
        self.encoder = BasePytorchEncoder.load_yaml(self.inception_yaml)
        vec = self.encoder.encode(self.test_img)
        self.assertEqual(vec.shape[0], len(self.test_img))
        self.assertEqual(vec.shape[1], 2048)

    def test_dump_load(self):
        self.encoder = BasePytorchEncoder.load_yaml(self.vgg_yaml)

        self.encoder.dump(self.dump_path)

        vgg_encoder2 = BasePytorchEncoder.load(self.dump_path)

        vec = vgg_encoder2.encode(self.test_img)
        self.assertEqual(vec.shape[0], len(self.test_img))
        self.assertEqual(vec.shape[1], 4096)

    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)
