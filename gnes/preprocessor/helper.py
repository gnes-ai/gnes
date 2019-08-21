#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the 'License');
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an 'AS IS' BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import datetime
import io
import os
import subprocess as sp
from datetime import timedelta
from itertools import product
from typing import List, Callable

import cv2
import numpy as np
from PIL import Image

from ..helper import set_logger

logger = set_logger(__name__, True)


def get_video_length(video_path):
    import re
    process = sp.Popen(['ffmpeg', '-i', video_path],
                       stdout=sp.PIPE,
                       stderr=sp.STDOUT)
    stdout, _ = process.communicate()
    stdout = str(stdout)
    matches = re.search(r"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),", stdout,
                        re.DOTALL).groupdict()
    h = float(matches['hours'])
    m = float(matches['minutes'])
    s = float(matches['seconds'])

    return 3600 * h + 60 * m + s


def get_video_length_from_raw(buffer_data):
    import re
    ffmpeg_cmd = ['ffmpeg', '-i', '-', '-']
    with sp.Popen(ffmpeg_cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE,
                  bufsize=-1, shell=False) as pipe:
        _, stdout = pipe.communicate(buffer_data)
        stdout = stdout.decode()
        matches = re.search(r"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?),", stdout,
                            re.DOTALL).groupdict()
        h = str(int(matches['hours']))
        m = str(int(matches['minutes']))
        s = str(round(float(matches['seconds'])))
        duration = datetime.datetime.strptime(h + ':' + m + ':' + s, '%H:%M:%S')
    return duration


def get_audio(buffer_data, sample_rate, interval,
              duration) -> List['np.ndarray']:
    import soundfile as sf

    audio_list = []
    start_time = datetime.datetime.strptime('00:00:00', '%H:%M:%S')
    while True:
        if start_time == duration:
            break

        end_time = start_time + timedelta(seconds=interval)
        if end_time > duration:
            end_time = duration
        ffmpeg_cmd = ['ffmpeg', '-i', '-',
                      '-f', 'wav',
                      '-ar', str(sample_rate),
                      '-ss', str(start_time).split(' ')[1],
                      '-to', str(end_time).split(' ')[1],
                      '-']

        # (-f, wav) output bytes in wav format
        # (-ar) sample rate
        # (-) output to stdout pipeline

        with sp.Popen(
                ffmpeg_cmd, stdin=sp.PIPE, stdout=sp.PIPE, bufsize=-1,
                shell=False) as pipe:
            raw_audio, _ = pipe.communicate(buffer_data)
            tmp_stream = io.BytesIO(raw_audio)
            data, sample_rate = sf.read(tmp_stream)
            # has multiple channels, do average
            if len(data.shape) == 2:
                data = np.mean(data, axis=1)
            if data.shape[0] != 0:
                audio_list.append(data)

        start_time = end_time

    return audio_list


def split_mp4_random(video_path, avg_length, max_clip_second=10):
    import random
    l = get_video_length(video_path)
    s = []
    num_part = max(int(l / avg_length), 2)

    while sum(s) < l:
        s.append(random.randint(3, max_clip_second))
    s[-1] = int(l - sum(s[:-1]))
    start = [sum(s[:i]) for i in range(len(s))]

    ts_group = [[] for _ in range(num_part)]

    for i, (_start, _du) in enumerate(zip(start, s)):
        ts_group[i % num_part].append(' -ss {} -t {} -i {} '.format(_start, _du, video_path))

    prefix = os.path.basename(video_path).replace('.mp4', '')
    for i in range(num_part):
        i_len = len(ts_group[i])
        cmd = 'ffmpeg' + ''.join(
            ts_group[i]) + '-filter_complex "{}concat=n={}:v=1:a=1" -strict -2 {}_{}.mp4 -y'.format(
            ''.join(['[{}]'.format(k) for k in range(i_len)]), i_len, prefix, i)
        os.system(cmd)


def get_video_frames(buffer_data: bytes, image_format: str = 'cv2',
                     **kwargs) -> List['np.ndarray']:
    ffmpeg_cmd = ['ffmpeg', '-i', '-', '-f', 'image2pipe']

    # example k,v pair:
    #    (-s, 420*360)
    #    (-vsync, vfr)
    #    (-r, 10)
    for k, v in kwargs.items():
        if isinstance(v, (float, int)):
            v = str(v)
        ffmpeg_cmd.append('-' + k)
        ffmpeg_cmd.append(v)

    # (-c:v, png) output bytes in png format
    # (-an, -sn) disable audio processing
    # (-) output to stdout pipeline
    ffmpeg_cmd += ['-c:v', 'png', '-an', '-sn', '-']

    with sp.Popen(
            ffmpeg_cmd, stdin=sp.PIPE, stdout=sp.PIPE, bufsize=-1,
            shell=False) as pipe:
        stream, _ = pipe.communicate(buffer_data)

        # raw bytes for multiple PNGs.
        # split by PNG EOF b'\x89PNG'
        stream = stream.split(b'\x89PNG')

        if len(stream) <= 1:
            return []

        # reformulate the full pngs for feature processings.
        if image_format == 'pil':
            frames = [
                Image.open(io.BytesIO(b'\x89PNG' + _)) for _ in stream[1:]
            ]
        elif image_format == 'cv2':
            # frames = [
            #     cv2.imdecode(np.frombuffer(b'\x89PNG' + _, np.uint8), cv2.IMREAD_COLOR)
            #     for _ in stream[1:]
            # ]

            # TODO: to figure out the exception reason
            frames = []
            for _ in stream[1:]:
                image = cv2.imdecode(np.frombuffer(b'\x89PNG' + _, np.uint8), cv2.IMREAD_COLOR)
                try:
                    cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    frames.append(image)
                except Exception as e:
                    logger.warning(
                        "The decoded cv2 image from keyframe buffer can not be converted to RGB: %s" % str(e))
        else:
            logger.error("The image format [%s] is not supported so far!" % image_format)
            raise NotImplementedError

    return frames


def split_video_frames(buffer_data: bytes,
                       splitter: str = '__split__'):
    chunks = buffer_data.split(splitter.encode())
    return [np.array(Image.open(io.BytesIO(chunk))) for chunk in chunks]


def get_gif(images, fps=4):
    cmd = ['ffmpeg', '-y',
           '-f', 'rawvideo',
           '-vcodec', 'rawvideo',
           '-r', '%.02f' % fps,
           '-s', '%dx%d' % (images[0].shape[1], images[0].shape[0]),
           '-pix_fmt', 'rgb24',
           '-i', '-',
           '-filter_complex', '[0:v]split[x][z];[z]palettegen[y];[x]fifo[x];[x][y]paletteuse',
           '-r', '%.02f' % fps,
           '-f', 'gif',
           '-']
    with sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, bufsize=-1, shell=False) as pipe:
        for image in images:
            pipe.stdin.write(image.tostring())
        out, _ = pipe.communicate()
    return out


def block_descriptor(image: 'np.ndarray',
                     descriptor_fn: Callable,
                     num_blocks: int = 3) -> 'np.ndarray':
    h, w, _ = image.shape  # find shape of image and channel
    block_h = int(np.ceil(h / num_blocks))
    block_w = int(np.ceil(w / num_blocks))

    descriptors = []
    for i in range(0, h, block_h):
        for j in range(0, w, block_w):
            block = image[i:i + block_h, j:j + block_w]
            descriptors.extend(descriptor_fn(block))

    return np.array(descriptors)


def pyramid_descriptor(image: 'np.ndarray',
                       descriptor_fn: Callable,
                       max_level: int = 2) -> 'np.ndarray':
    descriptors = []
    for level in range(max_level + 1):
        num_blocks = 2 ** level
        descriptors.extend(block_descriptor(image, descriptor_fn, num_blocks))

    return np.array(descriptors)


def bgr_histogram(image: 'np.ndarray') -> 'np.ndarray':
    _, _, c = image.shape
    hist = [
        cv2.calcHist([image], [i], None, [256], [0, 256]) for i in range(c)
    ]
    # normalize hist
    hist = np.array([h / np.sum(h) for h in hist]).flatten()
    return hist


def hsv_histogram(image: 'np.ndarray') -> 'np.ndarray':
    _, _, c = image.shape
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # sizes = [180, 256, 256]
    # ranges = [(0, 180), (0, 256), (0, 256)]

    # hist = [
    #     cv2.calcHist([hsv], [i], None, [sizes[i]], ranges[i]) for i in range(c)
    # ]

    hist = [cv2.calcHist([hsv], [i], None, [256], [0, 256]) for i in range(c)]
    # normalize hist
    hist = np.array([h / np.sum(h) for h in hist]).flatten()
    return hist


def edge_detect(image: 'np.ndarray', **kwargs) -> 'np.ndarray':
    arg_dict = {
        'compute_threshold': True,
        'low_threshold': 0,
        'high_threshold': 200,
        'sigma': 0.5,
        'gauss_kernel': (9, 9),
        'L2': True
    }
    for k, v in kwargs.items():
        if k in arg_dict.keys():
            arg_dict[k] = v

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # add threshold for canny
    low_threshold = arg_dict['low_threshold']
    high_threshold = arg_dict['high_threshold']
    if arg_dict['compute_threshold']:
        # apply automatic Canny edge detection using the computed median
        v = np.median(image)
        sigma = arg_dict['sigma']
        low_threshold = ((1.0 - sigma) * v).astype("float32")
        high_threshold = ((1.0 + sigma) * v).astype("float32")
    tmp_image = cv2.GaussianBlur(image, arg_dict['gauss_kernel'], 1.2)
    edge_image = cv2.Canny(tmp_image, low_threshold, high_threshold, L2gradient=arg_dict['L2'])
    return edge_image


def phash_descriptor(image: 'np.ndarray'):
    image = Image.fromarray(image)
    import imagehash
    return imagehash.phash(image)


def compute_descriptor(image: 'np.ndarray',
                       method: str = 'bgr_histogram',
                       **kwargs) -> 'np.array':
    funcs = {
        'bgr_histogram': bgr_histogram,
        'hsv_histogram': hsv_histogram,
        'edge_detect': lambda image: edge_detect(image, **kwargs),
        'block_bgr_histogram': lambda image: block_descriptor(image, bgr_histogram, kwargs.get('num_blocks', 3)),
        'block_hsv_histogram': lambda image: block_descriptor(image, hsv_histogram, kwargs.get('num_blocks', 3)),
        'pyramid_bgr_histogram': lambda image: pyramid_descriptor(image, bgr_histogram, kwargs.get('max_level', 2)),
        'pyramid_hsv_histogram': lambda image: pyramid_descriptor(image, hsv_histogram, kwargs.get('max_level', 2)),
    }
    return funcs[method](image)


def compare_ecr(descriptors: List['np.ndarray'], dilate_rate: int = 5, neigh_avg: int = 2) -> List[float]:
    """ Apply the Edge Change Ratio Algorithm"""
    divd = lambda x, y: 0 if y == 0 else x / y

    dicts = []
    inv_dilate = []
    sum_disc = []
    for descriptor in descriptors:
        sum_disc.append(np.sum(descriptor))
        inv_dilate.append(255 - cv2.dilate(descriptor, np.ones((dilate_rate, dilate_rate))))

    for i in range(1, len(descriptors)):
        dict_0 = divd(float(np.sum(descriptors[i - 1] & inv_dilate[i])), float(sum_disc[i - 1]))
        dict_1 = divd(float(np.sum(descriptors[i] & inv_dilate[i - 1])), float(sum_disc[i]))
        tmp_dict = max(dict_0, dict_1)
        if i > 10:
            dict_0 = divd(float(np.sum(descriptors[i - 10] & inv_dilate[i])), float(sum_disc[i - 10]))
            dict_1 = divd(float(np.sum(descriptors[i] & inv_dilate[i - 10])), float(sum_disc[i]))
            tmp_dict *= (1 + max(dict_0, dict_1))
        dicts.append(tmp_dict)

    for _ in range(neigh_avg):
        tmp_dict = []
        for i in range(1, len(dicts) - 1):
            tmp_dict.append(max(dicts[i - 1], dicts[i], dicts[i + 1]))
        dicts = tmp_dict.copy()

    return dicts


def compare_descriptor(descriptor1: 'np.ndarray',
                       descriptor2: 'np.ndarray',
                       metric: str = 'chisqr') -> float:
    dist_metric = {
        'correlation': cv2.HISTCMP_CORREL,
        'chisqr': cv2.HISTCMP_CHISQR,
        'chisqr_alt': cv2.HISTCMP_CHISQR_ALT,
        'intersection': cv2.HISTCMP_INTERSECT,
        'bhattacharya': cv2.HISTCMP_BHATTACHARYYA,
        'hellinguer': cv2.HISTCMP_HELLINGER,
        'kl_div': cv2.HISTCMP_KL_DIV
    }

    return cv2.compareHist(descriptor1, descriptor2, dist_metric[metric])


def kmeans_algo(distances: List[float], **kwargs) -> List[int]:
    from sklearn.cluster import KMeans
    clt = KMeans(n_clusters=2)
    clt.fit(distances)

    num_frames = len(distances) + 1
    # select which cluster includes shot frames
    big_center = np.argmax(clt.cluster_centers_)

    shots = []
    shots.append(0)
    for i in range(0, len(clt.labels_)):
        if big_center == clt.labels_[i]:
            shots.append((i + 2))
    if shots[-1] < num_frames:
        shots.append(num_frames)
    else:
        shots[-1] = num_frames
    return shots


def check_motion(prev_dists: List[float], cur_dist: float, motion_threshold: float = 0.75):
    """ Returns a boolean value to decide if the peak is due to a motion"""
    close_peaks = 0
    # We observe the a defined number of frames before the peak
    for dist in prev_dists:
        if dist > cur_dist * motion_threshold:
            close_peaks += 1
    if close_peaks >= len(prev_dists) / 2:
        return True
    else:
        return False


def thre_algo(distances: List[float], **kwargs) -> List[int]:
    # now threshold algo not support motion
    kwargs['motion_step'] = 0
    return motion_algo(distances, **kwargs)


def motion_algo(distances: List[float], **kwargs) -> List[int]:
    import peakutils
    """ Returns the list of peaks in the ECR serie"""
    arg_dict = {
        'threshold': 0.6,
        'min_dist': 10,
        'motion_step': 15
    }
    shots = []
    for k, v in kwargs.items():
        if k in arg_dict.keys():
            arg_dict[k] = v
    num_frames = len(distances) + 1
    p = peakutils.indexes(np.array(distances).astype('float32'), thres=arg_dict['threshold'], min_dist=arg_dict['min_dist'])
    shots.append(0)
    shots.append(p[0] + 2)
    for i in range(1, len(p)):
        # We check that the peak is not due to a motion in the image
        valid_dist = arg_dict['motion_step'] or not check_motion(distances[p[i]-arg_dict['motion_step']:p[i]], distances[p[i]])
        if valid_dist:
            shots.append(p[i] + 2)
    if shots[-1] < num_frames - arg_dict['min_dist']:
        shots.append(num_frames)
    elif shots[-1] > num_frames:
        shots[-1] = num_frames
    return shots


def detect_video_shot(distances: List[float],
                      method: str = 'kmeans',
                      **kwargs) -> List[int]:
    detect_method = {
        'kmeans': kmeans_algo,
        'threshold': thre_algo,
        'motion': motion_algo
    }

    if method in detect_method.keys():
        return detect_method[method](distances, **kwargs)
    else:
        logger.error("detect video shot by [%s] not implemented! Please use threshold, kmeans or motion!" % method)


def torch_transform(img):
    import torchvision.transforms as transforms
    return transforms.Compose([transforms.ToTensor(),
                               transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))])(img)


def get_all_subarea(img):
    x_list = [0, img.size[0] / 3, 2 * img.size[0] / 3, img.size[0]]
    y_list = [0, img.size[1] / 3, 2 * img.size[1] / 3, img.size[1]]

    index = [[x, y, x + 1, y + 1] for [x, y] in product(range(len(x_list) - 1), range(len(y_list) - 1))]
    all_subareas = [[x_list[idx[0]], y_list[idx[1]], x_list[idx[2]], y_list[idx[3]]] for idx in index]
    return all_subareas, index
