import unittest
from gnes.proto import gnes_pb2, array2blob, blob2array
from gnes.preprocessor.video.frame_select import FrameSelectPreprocessor
import numpy as np
import copy


class TestFrameSelector(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = gnes_pb2.Document()

        c1 = self.doc.chunks.add()
        c1.blob.CopyFrom(array2blob(np.array([[1,2,3], [2,3,4]])))

        c2 = self.doc.chunks.add()
        c2.blob.CopyFrom(array2blob(np.array([[1,2,3], [2,3,4], [1,2,3]])))

        c3 = self.doc.chunks.add()
        c3.blob.CopyFrom(array2blob(np.array([[1,2,3], [2,3,4], [1,2,3], [2,3,4]])))

    def test_emtpy_document(self):
        frame_selector = FrameSelectPreprocessor(sframes=-1)
        frame_selector.apply(gnes_pb2.Document())

    def test_big_sframe(self):
        doc = copy.deepcopy(self.doc)
        frame_selector = FrameSelectPreprocessor(sframes=100)
        frame_selector.apply(doc)

    def test_get_frames(self):
        doc = copy.deepcopy(self.doc)
        frame_selector = FrameSelectPreprocessor(sframes=3)
        frame_selector.apply(doc)
        for idx, chunk in enumerate(doc.chunks):
            if idx == 0:
                self.assertEqual(blob2array(chunk.blob).shape[0], 2)
            else:
                self.assertEqual(blob2array(chunk.blob).shape[0], 3)

    def test_get_one_frame(self):
        doc = copy.deepcopy(self.doc)
        frame_selector = FrameSelectPreprocessor(sframes=1)
        frame_selector.apply(doc)
        for chunk in doc.chunks:
            self.assertEqual(blob2array(chunk.blob).shape[0], 1)




