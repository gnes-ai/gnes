import os
import unittest

from gnes.encoder.audio.mfcc import MfccEncoder
from gnes.preprocessor.helper import get_audio, get_video_length_from_raw


def extract_audio(video_bytes):
    sample_rate = 6500
    audio_interval = 1
    audios = []
    for raw_bytes in video_bytes:
        audio = get_audio(raw_bytes, sample_rate, audio_interval, get_video_length_from_raw(raw_bytes))
        audios.append(audio)
    audios = [slice for audio in audios for slice in audio]
    return audios


class TestMfccEncoder(unittest.TestCase):

    def setUp(self):
        self.dirname = os.path.dirname(__file__)
        self.video_path = os.path.join(self.dirname, 'videos')
        self.video_bytes = [open(os.path.join(self.video_path, _), 'rb').read()
                            for _ in os.listdir(self.video_path)]
        self.audios = extract_audio(self.video_bytes)
        self.mfcc_yaml = os.path.join(self.dirname, 'yaml', 'mfcc-encoder.yml')

    def test_mfcc_encoding(self):
        self.encoder = MfccEncoder.load_yaml(self.mfcc_yaml)
        vec = self.encoder.encode(self.audios)
        self.assertEqual(len(vec.shape), 2)
        self.assertEqual(vec.shape[0], len(self.audios))
        self.assertEqual(vec.shape[1] % self.encoder.n_mfcc, 0)
