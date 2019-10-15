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

from typing import List

def encode_video(images: List['np.ndarray'], frame_rate: int, pix_fmt: str = 'rgb24'):
    import webp
    from PIL import Image

    height, width, _ = images[0].shape
    if pix_fmt == 'rgb24':
        pix_fmt = 'RGB'
    # Save an animation
    enc = webp.WebPAnimEncoder.new(width, height)
    timestamp_ms = 0
    duration = 1000 // frame_rate
    for x in images:
        img = Image.fromarray(x.copy(), pix_fmt)
        pic = webp.WebPPicture.from_pil(img)
        enc.encode_frame(pic, timestamp_ms)
        timestamp_ms += duration
    anim_data = enc.assemble(timestamp_ms)
    return bytes(anim_data.buffer())
