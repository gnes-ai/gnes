# cython: language_level=3

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

# pylint: disable=low-comment-ratio.

ctypedef float DIST
ctypedef unsigned int UINT
ctypedef unsigned short USHORT
ctypedef unsigned char UCHAR
ctypedef UCHAR* BVECTOR
ctypedef unsigned int UIDX

cdef struct hnsw_edge:
    hnswNode* node
    DIST dist
    hnsw_edge* next

cdef struct hnsw_edge_set:
    hnsw_edge* head_ptr
    hnsw_edge* last_ptr
    USHORT size

    USHORT indegree

cdef struct hnswNode:
    UIDX id
    BVECTOR vector
    USHORT level
    USHORT low_level
    hnsw_edge_set** edges
    hnswNode* next

cdef struct hnswConfig:
    float level_multiplier
    int ef
    int ef_construction
    int m
    int m_max
    int m_max_0
    float epsilon