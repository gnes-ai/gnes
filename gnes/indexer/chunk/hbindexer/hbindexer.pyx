# cython: language_level=3, wraparound=False, boundscheck=False, cdivision=True
# noinspection PyUnresolvedReferences
# created 2019-03-27

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

# pylint: disable=low-comment-ratio


from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from cpython cimport array
from libc.stdlib cimport qsort
from libc.stdio cimport fopen, fclose, FILE, fwrite, fread


cdef extern from "limits.h":
    cdef int USHRT_MAX
    cdef unsigned int UINT_MAX

short_max = USHRT_MAX
int_max = UINT_MAX
DEF Increase = 10000

ctypedef unsigned int uint
ctypedef unsigned short ushort
ctypedef unsigned char uchar

cdef uint bytes_to_uint(uchar*all_ids):
    cdef uint label
    cdef ushort _
    label = 0
    for _ in range(4):
        label += (256**_) * all_ids[_]
    return label

cdef ushort bytes_to_ushort(uchar*all_ids):
    cdef ushort offset
    offset = all_ids[0] + all_ids[1]*256
    return offset


cdef ushort vec_distance(uchar*va, uchar*vb, ushort bytes_per_vector):
    cdef ushort i, dist
    dist = 0
    cdef uchar tmp_vec
    for i in range(bytes_per_vector):
        a = va[i]
        b = vb[i]
        tmp_vec = (a ^ b)

        while tmp_vec > 0:
            dist += tmp_vec & 1
            tmp_vec >>= 1
    return dist

cdef struct res_node:
    uint doc_id
    ushort off_set
    ushort weight
    uint dist


cdef void max_heapify(res_node* ret, int loc, int count):
    cdef int left, right, largest
    cdef uint temp
    cdef ushort temp2, temp3
    left = 2*(loc) + 1
    right = left + 1
    largest = loc

    if left < count:
        if ret[left].dist > ret[largest].dist:
            largest = left

    if right < count:
        if ret[right].dist > ret[largest].dist:
            largest = right

    if(largest != loc):
        temp = ret[loc].doc_id
        ret[loc].doc_id = ret[largest].doc_id
        ret[largest].doc_id = temp

        temp = ret[loc].dist
        ret[loc].dist = ret[largest].dist
        ret[largest].dist = temp

        temp2 = ret[loc].off_set
        ret[loc].off_set = ret[largest].off_set
        ret[largest].off_set = temp2

        temp3 = ret[loc].weight
        ret[loc].weight = ret[largest].weight
        ret[largest].weight = temp3

        max_heapify(ret, largest, count)


cdef void heap_push(res_node* ret, uint value, uint doc_id, ushort off_set, ushort weight, int count):
    cdef int index, parent
    index = count
    if index == 0:
        ret[0].dist = value
        ret[0].doc_id = doc_id
        ret[0].off_set = off_set
        ret[0].weight = weight
    else:
        parent = (index - 1)/2
        while (ret[parent].dist < value):
            if index <= 0:
                break
            ret[index].dist = ret[parent].dist
            ret[index].doc_id = ret[parent].doc_id
            ret[index].off_set = ret[parent].off_set
            ret[index].weight = ret[parent].weight
            index = parent
            parent = (index - 1)/2
        ret[index].dist = value
        ret[index].doc_id = doc_id
        ret[index].off_set = off_set
        ret[index].weight = weight


cdef class IndexCore:
    cdef uchar* vecs
    cdef uint n_clusters
    cdef uint n_bytes
    cdef uint n_idx
    cdef uint i
    cdef uchar initialized
    cdef uchar*** core
    cdef uint** data_num

    def __cinit__(self, n_clusters, n_bytes, n_idx):
        self.n_clusters = n_clusters
        self.n_bytes = n_bytes
        self.n_idx = n_idx
        self.core = <uchar***> PyMem_Malloc(sizeof(uchar**)*n_idx)
        self.data_num = <uint**> PyMem_Malloc(sizeof(uint*)*n_idx)
        for i in range(self.n_idx):
            self.core[i] = <uchar**> PyMem_Malloc(sizeof(uchar*)*self.n_clusters)
        self.initialized = 0

    cdef void _initialize(self):
        cdef uint i, j
        for i in range(self.n_idx):
            for j in range(self.n_clusters):
                self.core[i][j] = <uchar*> PyMem_Malloc(sizeof(uchar)*(self.n_bytes+8)*Increase)
            # initialized the default value of num of data in each array
            self.data_num[i] = <uint*> PyMem_Malloc(sizeof(uint)*self.n_clusters)
            for j in range(self.n_clusters):
                self.data_num[i][j] = 0

    cpdef void index_trie(self, uchar*data, uchar*clusters, uchar*doc_ids, uchar*off_sets, uchar* weights, uint n):
        cdef uint i, clus, num, cur_num
        cdef ushort j, k
        cdef uchar*vec
        if not self.initialized:
            self._initialize()
            self.initialized = 1
        for i in range(n):
            vec = data + 4 * self.n_idx
            for j in range(self.n_idx):
                clus = bytes_to_uint(clusters)
                num = self.data_num[j][clus]
                cur_num = num * (self.n_bytes + 8)
                if (num + 1) % Increase == 0:
                    self.core[j][clus] = <uchar*> PyMem_Realloc(
                        self.core[j][clus],
                        sizeof(uchar)*(self.n_bytes+8)*(num+1+Increase))
                # record doc id
                for k in range(4):
                    self.core[j][clus][cur_num+k] = doc_ids[k]
                cur_num += 4
                # record offset
                for k in range(2):
                    self.core[j][clus][cur_num+k] = off_sets[k]
                cur_num += 2
                for k in range(2):
                    self.core[j][clus][cur_num+k] = weights[k]
                cur_num += 2
                for k in range(self.n_bytes):
                    self.core[j][clus][cur_num+k] = data[k]
                clusters += 4
                self.data_num[j][clus] += 1

            data += self.n_bytes
            doc_ids += 4
            off_sets += 2
            weights += 2

    cpdef query(self, uchar*data, uchar*clusters, uint n, uint top_k):
        cdef array.array res_dist = array.array('L')
        cdef array.array res_docs = array.array('L')
        cdef array.array res_offset = array.array('L')
        cdef array.array res_weight = array.array('L')
        cdef array.array res_idx = array.array('L')

        cdef uint _0, _1, i
        cdef ushort _2
        cdef uchar*vec
        cdef uchar*id_offset
        cdef uint*res
        cdef uint doc_id, dist
        cdef ushort off_set, weight
        cdef int count

        ret = <res_node*> PyMem_Malloc(sizeof(res_node)*top_k)

        for _0 in range(n):
            count = 0
            for _1 in range(self.n_idx):
                clus = bytes_to_uint(clusters)
                vec = self.core[_1][clus]
                for i in range(self.data_num[_1][clus]):
                    # dynamic update result list
                    dist = vec_distance(vec + 8, data, self.n_bytes)
                    if count < top_k:
                        doc_id = bytes_to_uint(vec)
                        off_set = bytes_to_ushort(vec+4)
                        weight = bytes_to_ushort(vec+6)
                        heap_push(ret, dist, doc_id, off_set, weight, count)
                        count += 1
                    elif dist < ret[0].dist:
                        doc_id = bytes_to_uint(vec)
                        off_set = bytes_to_ushort(vec+4)
                        weight = bytes_to_ushort(vec+6)
                        ret[0].dist = dist
                        ret[0].doc_id = doc_id
                        ret[0].off_set = off_set
                        ret[0].weight = weight
                        max_heapify(ret, 0, count)
                    vec += self.n_bytes + 8
                clusters += 4
            for _1 in range(top_k):
                res_dist.append(ret[_1].dist)
                res_docs.append(ret[_1].doc_id)
                res_offset.append(ret[_1].off_set)
                res_weight.append(ret[_1].weight)
                res_idx.append(_0)

            data += self.n_bytes
        PyMem_Free(ret)

        return res_docs, res_offset, res_weight, res_dist, res_idx

    cdef void _save(self, char*save_path):
        cdef FILE*save_file
        cdef uint i, j, num
        save_file = fopen(save_path, "wb")
        fwrite(&self.n_clusters, sizeof(uint), 1, save_file)
        fwrite(&self.n_bytes, sizeof(uint), 1, save_file)
        fwrite(&self.n_idx, sizeof(uint), 1, save_file)
        for i in range(self.n_idx):
            fwrite(self.data_num[i], sizeof(uint), self.n_clusters, save_file)
        for i in range(self.n_idx):
            for j in range(self.n_clusters):
                num = ((self.data_num[i][j] + 1) / Increase + 1)*Increase
                fwrite(self.core[i][j], sizeof(uchar), (self.n_bytes+8)*num, save_file)

    cdef void _load(self, char*load_path):
        cdef FILE*load_file
        cdef uint i, j, num
        load_file = fopen(load_path, "rb")
        fread(&self.n_clusters, sizeof(uint), 1, load_file)
        fread(&self.n_bytes, sizeof(uint), 1, load_file)
        fread(&self.n_idx, sizeof(uint), 1, load_file)
        for i in range(self.n_idx):
            tmp = <uint*> PyMem_Malloc(sizeof(uint)*self.n_clusters)
            fread(tmp, sizeof(uint), self.n_clusters, load_file)
            self.data_num[i] = tmp
        for i in range(self.n_idx):
            for j in range(self.n_clusters):
                num = ((self.data_num[i][j] + 1) / Increase + 1)*Increase
                tmp2 = <uchar*> PyMem_Malloc(sizeof(uchar)*(self.n_bytes+8)*num)
                fread(tmp2, sizeof(uchar), (self.n_bytes+8)*num, load_file)
                self.core[i][j] = tmp2
        self.initialized = 1

    def destroy(self):
        self.free_trie()

    cdef void free_trie(self):
        for i in range(self.n_idx):
            PyMem_Free(self.data_num[i])
        for i in range(self.n_idx):
            for j in range(self.n_clusters):
                PyMem_Free(self.core[i][j])

    def save(self, save_path):
        self._save(bytes(save_path, 'utf8'))

    def load(self, load_path):
        self._load(bytes(load_path, 'utf8'))