import copy
import os
import unittest

import numpy as np
from gnes.proto import gnes_pb2, array2blob

from gnes.preprocessor.base import BaseVideoPreprocessor


class TestVideoEncoder(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.mp4_yaml_path = os.path.join(self.dirname, 'yaml', 'mp4-encoder.yml')
        self.gif_yaml_path = os.path.join(self.dirname, 'yaml', 'gif-encoder.yml')
        self.dump_path = os.path.join(self.dirname, 'video_encoder.bin')
        self.frames_path = os.path.join(self.dirname, 'frames', 'frames.npy')
        self.mp4_encoder = BaseVideoPreprocessor.load_yaml(self.mp4_yaml_path)
        self.gif_encoder = BaseVideoPreprocessor.load_yaml(self.gif_yaml_path)
        self.video_frames = np.load(self.frames_path)


    def test_mp4_encoder(self):
        raw_data = array2blob(self.video_frames)

        doc = gnes_pb2.Document()
        doc.doc_type = gnes_pb2.Document.VIDEO
        doc.raw_video.CopyFrom(raw_data)
        self.mp4_encoder.apply(doc)
        doc1 = copy.deepcopy(doc)

        doc = gnes_pb2.Document()
        doc.doc_type = gnes_pb2.Document.VIDEO
        chunk = doc.chunks.add()
        chunk.blob.CopyFrom(raw_data)
        self.mp4_encoder.apply(doc)
        doc2 = copy.deepcopy(doc)

        self.assertEqual(doc1.raw_bytes, doc2.chunks[0].raw)

    def test_gif_encoder(self):
        raw_data = array2blob(self.video_frames)

        doc = gnes_pb2.Document()
        doc.doc_type = gnes_pb2.Document.VIDEO
        doc.raw_video.CopyFrom(raw_data)
        self.gif_encoder.apply(doc)
        doc1 = copy.deepcopy(doc)

        doc = gnes_pb2.Document()
        doc.doc_type = gnes_pb2.Document.VIDEO
        chunk = doc.chunks.add()
        chunk.blob.CopyFrom(raw_data)
        self.gif_encoder.apply(doc)
        doc2 = copy.deepcopy(doc)

        self.assertEqual(doc1.raw_bytes, doc2.chunks[0].raw)

    def test_empty_doc(self):
        doc = gnes_pb2.Document()
        doc.doc_type = gnes_pb2.Document.VIDEO
        self.mp4_encoder.apply(doc)

    def test_dump_load(self):
        raw_data = array2blob(self.video_frames)

        doc = gnes_pb2.Document()
        doc.doc_type = gnes_pb2.Document.VIDEO
        doc.raw_video.CopyFrom(raw_data)
        self.mp4_encoder.apply(doc)
        doc1 = copy.deepcopy(doc)

        self.mp4_encoder.dump(self.dump_path)

        encoder = BaseVideoPreprocessor.load(self.dump_path)

        doc = gnes_pb2.Document()
        doc.doc_type = gnes_pb2.Document.VIDEO
        chunk = doc.chunks.add()
        chunk.blob.CopyFrom(raw_data)
        encoder.apply(doc)
        doc2 = copy.deepcopy(doc)

        self.assertEqual(doc1.raw_bytes, doc2.chunks[0].raw)


    def tearDown(self):
        if os.path.exists(self.dump_path):
            os.remove(self.dump_path)
