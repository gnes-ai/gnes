import copy
import os
import unittest

from gnes.preprocessor.io_utils import ffmpeg
from gnes.preprocessor.io_utils import video
from gnes.preprocessor.io_utils import gif
from gnes.preprocessor.io_utils import audio


class TestFFmpeg(unittest.TestCase):
    def setUp(self):
        self.dirname = os.path.dirname(__file__)

        self.video_path = os.path.join(self.dirname, 'videos', 'test.mp4')
        self.frames = video.capture_frames(input_fn=self.video_path, fps=10, scale='640:360')

    def test_probe(self):
        probe = ffmpeg.probe(self.video_path)
        self.assertEqual(probe['height'], 720)
        self.assertEqual(probe['width'], 1280)
        self.assertEqual(probe['fps'], 25.0)


    def test_get_media_meta(self):
        meta1 = ffmpeg.get_media_meta(input_fn=self.video_path)
        with open(self.video_path, 'rb') as f:
            data = f.read()
            meta2 = ffmpeg.get_media_meta(input_data=data)
        self.assertEqual(meta1['frame_width'], meta2['frame_width'])
        self.assertEqual(meta1['frame_height'], meta2['frame_height'])

    def test_capture_frames(self):
        frames1 = video.capture_frames(input_fn=self.video_path, fps=10, scale='640:-2')
        sub_frames = video.capture_frames(input_fn=self.video_path, fps=10, scale='640:-2', vframes=5)
        self.assertEqual((sub_frames == frames1[:5]).all(), True)

        with open(self.video_path, 'rb') as f:
            data = f.read()
            frames2 = video.capture_frames(input_data=data, fps=10, scale='-1:360')

        self.assertEqual(frames1.shape, frames2.shape)

    def test_scale_video(self):
        out = video.scale_video(input_fn=self.video_path, scale='640:360')
        meta = ffmpeg.get_media_meta(input_data=out, input_options={'format': 'mp4'})
        self.assertEqual(meta['frame_width'], 640)
        self.assertEqual(meta['frame_height'], 360)

    def test_encode_video(self):
        video_data = video.encode_video(images=self.frames)
        meta = ffmpeg.get_media_meta(input_data=video_data, input_options={'format': 'mp4'})
        self.assertEqual(meta['frame_width'], 640)
        self.assertEqual(meta['frame_height'], 360)

    def test_gif_encode(self):
        gif_data = gif.encode_video(images=self.frames, frame_rate=10)
        frames = gif.capture_frames(input_data=gif_data)
        sub_frames = gif.capture_frames(input_data=gif_data, vframes=5)
        self.assertEqual(self.frames.shape, frames.shape)
        self.assertEqual((sub_frames == frames[:5]).all(), True)

    def test_capture_audio(self):
        audio_data1 = audio.capture_audio(input_fn=self.video_path)
        with open(self.video_path, 'rb') as f:
            data = f.read()
            audio_data2 = audio.capture_audio(input_data=data)

            self.assertEqual(audio_data1.shape, audio_data2.shape)

    def test_split_audio(self):
        chunks1 = audio.split_audio(input_fn=self.video_path)
        with open(self.video_path, 'rb') as f:
            data = f.read()
            chunks2 = audio.split_audio(input_data=data)
            self.assertEqual(len(chunks1), len(chunks2))
            self.assertEqual(chunks1[0].shape, chunks2[0].shape)
