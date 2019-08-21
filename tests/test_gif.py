import copy
import os
import unittest

from gnes.preprocessor.base import BasePreprocessor
from gnes.preprocessor.video.ffmpeg import FFmpegVideoSegmentor
from gnes.proto import gnes_pb2


class TestPartition(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.p3_name = 'pipe-gif'
        self.pipeline_path = os.path.join(self.dirname, 'yaml/%s.yml' % self.p3_name)
        self.ffmpeg_yaml_path = os.path.join(self.dirname, 'yaml/preprocessor-ffmpeg2.yml')
        self.video_path = os.path.join(self.dirname, 'videos')
        self.video_bytes = [open(os.path.join(self.video_path, _), 'rb').read()
                            for _ in os.listdir(self.video_path)]

    def test_gif_pipelinepreproces(self):
        d = gnes_pb2.Document()
        d.raw_bytes = self.video_bytes[0]
        d_ = copy.deepcopy(d)

        p3 = FFmpegVideoSegmentor.load_yaml(self.ffmpeg_yaml_path)
        p3.apply(d)

        p4 = BasePreprocessor.load_yaml(self.pipeline_path)
        p4.apply(d_)

        self.assertEqual(len(d.chunks), len(d_.chunks))
