#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import numpy as np

from ..base import BaseAudioPreprocessor
from ...proto import array2blob, blob2array


class VggishPreprocessor(BaseAudioPreprocessor):

    def __init__(self, num_frames: int = 96,
                 num_bands: int = 64,
                 sample_rate: int = 16000,
                 log_offset: float = 0.01,
                 example_window_seconds: float = 0.96,
                 example_hop_seconds: float = 0.96,
                 stft_window_length_seconds: float = 0.025,
                 stft_hop_length_seconds: float = 0.01,
                 mel_min_hz: int = 125,
                 mel_max_hz: int = 7500,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_frames = num_frames
        self.num_bands = num_bands
        self.sample_rate = sample_rate
        self.log_offset = log_offset
        self.example_window_seconds = example_window_seconds
        self.example_hop_seconds = example_hop_seconds
        self.stft_window_length_seconds = stft_window_length_seconds
        self.stft_hop_length_seconds = stft_hop_length_seconds
        self.mel_min_hz = mel_min_hz
        self.mel_max_hz = mel_max_hz
        self.num_mel_binds = num_bands

    def apply(self, doc: 'gnes_pb2.Document') -> None:
        super().apply(doc)

        if doc.raw_bytes:
            for chunks in doc.chunks:
                chunks.blob.CopyFrom(array2blob(np.array(self.waveform_to_examples(blob2array(chunks.blob),
                                            sample_rate=self.sample_rate), dtype=np.float32)))
        else:
            self.logger.error('bad document: "raw_bytes" is empty!')

    def waveform_to_examples(self, data, sample_rate):
        """Converts audio waveform into an array of examples for VGGish.

        Args:
          data: np.array of either one dimension (mono) or two dimensions
            (multi-channel, with the outer dimension representing channels).
            Each sample is generally expected to lie in the range [-1.0, +1.0],
            although this is not required.
          sample_rate: Sample rate of data.

        Returns:
          3-D np.array of shape [num_examples, num_frames, num_bands] which represents
          a sequence of examples, each of which contains a patch of log mel
          spectrogram, covering num_frames frames of audio and num_bands mel frequency
          bands, where the frame length is vggish_params.STFT_HOP_LENGTH_SECONDS.
        """
        from .vggish_example_helper import mel_features
        import resampy

        # Convert to mono.
        print(type(data))
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        # Resample to the rate assumed by VGGish.
        if sample_rate != self.sample_rate:
            data = resampy.resample(data, sample_rate, self.sample_rate)

        # Compute log mel spectrogram features.
        log_mel = mel_features.log_mel_spectrogram(
            data,
            audio_sample_rate=self.sample_rate,
            log_offset=self.log_offset,
            window_length_secs=self.stft_window_length_seconds,
            hop_length_secs=self.stft_hop_length_seconds,
            num_mel_bins=self.num_mel_binds,
            lower_edge_hertz=self.mel_min_hz,
            upper_edge_hertz=self.mel_max_hz)

        # Frame features into examples.
        features_sample_rate = 1.0 / self.stft_hop_length_seconds
        example_window_length = int(round(
            self.example_window_seconds * features_sample_rate))
        example_hop_length = int(round(
            self.example_hop_seconds * features_sample_rate))
        log_mel_examples = mel_features.frame(
            log_mel,
            window_length=example_window_length,
            hop_length=example_hop_length)
        return log_mel_examples