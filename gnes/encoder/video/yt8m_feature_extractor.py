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

from typing import List
import numpy as np
from PIL import Image
from ..base import BaseVideoEncoder
from ...helper import batching, get_first_available_gpu


class YouTube8MFeatureExtractor(BaseVideoEncoder):
    """Extracts YouTube8M features for RGB frames.

    First time constructing this class will create directory `yt8m` inside your
    home directory, and will download inception model (85 MB) and YouTube8M PCA
    matrix (15 MB). If you want to use another directory, then pass it to argument
    `model_dir` of constructor.

    If the model_dir exist and contains the necessary files, then files will be
    re-used without download.

    Usage Example:

        from PIL import Image
        import numpy

        # Instantiate extractor. Slow if called first time on your machine, as it
        # needs to download 100 MB.
        extractor = YouTube8MFeatureExtractor()

        image_file = os.path.join(extractor._model_dir, 'cropped_panda.jpg')

        im = numpy.array(Image.open(image_file))
        features = extractor.extract_rgb_frame_features(im)

    ** Note: OpenCV reverses the order of channels (i.e. orders channels as BGR
    instead of RGB). If you are using OpenCV, then you must do:

        im = im[:, :, ::-1]  # Reverses order on last (i.e. channel) dimension.

    then call `extractor.extract_rgb_frame_features(im)`
    """
    batch_size = 64

    def __init__(self, model_dir: str,
                 pca_dir: str,
                 select_layer: str = 'PreLogits',
                 ignore_audio_feature: bool = True,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model_dir = model_dir
        self.pca_dir = pca_dir
        self.select_layer = select_layer
        self.ignore_audio_feature = ignore_audio_feature
        self.audio_dim = 128
        self.incep_dim = 2048
        self.pca_dim = 1024
        self.inception_size_x = 299
        self.inception_size_y = 299

    def post_init(self):
        import tensorflow as tf
        from .yt8m_feature_extractor_cores.inception_v3 import inception_v3
        from .yt8m_feature_extractor_cores.inception_utils import inception_arg_scope
        import os
        os.environ['CUDA_VISIBLE_DEVICES'] = str(get_first_available_gpu())

        self.pca_mean = np.load(os.path.join(self.pca_dir, 'mean.npy'))[:, 0]
        self.pca_eigenvals = np.load(os.path.join(self.pca_dir, 'eigenvals.npy'))[:self.pca_dim, 0]
        self.pca_eigenvecs = np.load(os.path.join(self.pca_dir, 'eigenvecs.npy')).T[:, :self.pca_dim]

        g = tf.Graph()
        with g.as_default():
            arg_scope = inception_arg_scope()
            inception_v3.default_image_size = self.inception_size_x
            self.inputs = tf.placeholder(tf.float32, (None,
                                                      self.inception_size_x,
                                                      self.inception_size_y, 3))

            with tf.contrib.slim.arg_scope(arg_scope):
                self.logits, self.end_points = inception_v3(self.inputs,
                                                            num_classes=1001,
                                                            is_training=False,
                                                            dropout_keep_prob=1.0)

            config = tf.ConfigProto(log_device_placement=False)
            if self.on_gpu:
                config.gpu_options.allow_growth = True
            self.sess = tf.Session(config=config)
            self.saver = tf.train.Saver()
            self.saver.restore(self.sess, self.model_dir)

    def encode(self, data: List['np.ndarray'], *args, **kwargs) -> List['np.ndarray']:
        video_length = [len(d) for d in data]
        for i in range(1, len(video_length)):
            video_length[i] = video_length[i] + video_length[i - 1]

        data = [(np.array(Image.fromarray(im).resize((self.inception_size_x,
                                                      self.inception_size_y)), dtype=np.float32) * 2 / 255. - 1.)
                for video in data for im in video]

        data = np.stack((list(data[i] for i in range(len(data)))), axis=0)

        @batching
        def _encode(_, data):
            def _pca(data):
                data = np.squeeze(data, axis=(1, 2))
                data = (data - self.pca_mean).reshape((len(data), self.incep_dim))
                data = np.matmul(data, self.pca_eigenvecs)
                data = data / np.sqrt(self.pca_eigenvals + 1e-4)
                return data

            _, end_points_ = self.sess.run((self.logits, self.end_points),
                                           feed_dict={self.inputs: data})
            data = _pca(end_points_[self.select_layer])
            return data

        def _fill_audio_feature(data):
            return list(map(lambda x: np.concatenate((x, np.zeros(shape=(x.shape[0], self.audio_dim))), axis=1), data))

        data = _encode(self, data)

        data = np.split(data, video_length[:-1])

        if self.ignore_audio_feature:
            return _fill_audio_feature(data)
        else:
            return data.astype(np.float32)

