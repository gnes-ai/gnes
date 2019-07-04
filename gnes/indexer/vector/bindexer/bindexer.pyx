# cython: language_level=3, wraparound=False, boundscheck=False
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
data_size_per_time = USHRT_MAX
node_size_per_time = USHRT_MAX
DEF data_blocks_increment = 100
DEF node_blocks_increment = 100

DEF search_v_max = 10000
DEF search_c_max = 10000
DEF search_w_max = 10000

ctypedef unsigned int UIDX
ctypedef unsigned short UST
ctypedef unsigned char UCR

cdef struct coordi:
    UST x
    UST y

cdef struct ncoordi:
    UST x
    UIDX y

cdef struct Node:
    coordi left
    coordi right
    coordi child
    coordi parent
    unsigned char key
    coordi _next

cdef struct Data:
    UIDX doc_id
    UST offset
    UST weight
    coordi _next
    ncoordi _neighbor
    coordi parent
    UST num_in
    UST num_out

cdef struct DataDist:
    Data*data
    UST dist
    coordi data_coordi

cdef UIDX bytes_to_label(UCR*all_ids, UST bytes_per_label):
    cdef UIDX label
    cdef UST _
    label = 0
    for _ in range(bytes_per_label):
        label += (256**_) * all_ids[_]
    return label

cdef UST bytes_to_offset(UCR*all_ids):
    cdef UST offset
    offset = all_ids[0] + all_ids[1]*256
    return offset


cdef int cmpfunc(const void*a, const void*b) nogil:
    cdef DataDist*av = <DataDist*>a
    cdef DataDist*bv = <DataDist*>b
    return av.dist - bv.dist

cdef DataDist*sort_Datadist(DataDist*W, UIDX wsize):
    qsort(W, wsize, sizeof(DataDist), &cmpfunc)
    return W

cdef UST vec_distance(UCR*va, UCR*vb, UST bytes_per_vector):
    cdef UST i, dist
    dist = 0

    #for i in prange(bytes_per_vector, num_threads=5):
    for i in range(bytes_per_vector):
        if va[i] != vb[i]:
            dist += 1
    return dist

cdef class IndexCore:
    cdef Node*root_node
    cdef UST bytes_per_vector
    cdef UST bytes_per_label
    cdef UST ef
    cdef UIDX max_insert_iterations
    cdef UIDX max_query_iterations

    cdef Data**all_data
    cdef Node**all_nodes
    cdef coordi**all_neigh
    cdef coordi NULL_coordi

    cdef UIDX nodes_capacity
    cdef UIDX data_capacity
    cdef UIDX max_data_blocks
    cdef UIDX max_node_blocks

    cdef UIDX cur_data_blocks
    cdef UIDX cur_node_blocks

    cdef UIDX num_nodes
    cdef UIDX num_data

    cdef UST num_entry
    cdef UST num_count
    cdef UST max_entry

    cdef UCR*cur_vec
    cdef DataDist*W
    cdef DataDist*C
    cdef Data**V
    cdef coordi*res
    cdef coordi*res_query
    cdef coordi*entry_node
    cdef UCR update_single_neighbor, debugging_mode, initialized

    def __cinit__(self, bytes_per_vector, bytes_per_label, ef,
                  max_insert_iterations=1000,
                  max_query_iterations=5000,
                  debugging_mode=0,
                  update_single_neighbor=1):
        self.bytes_per_vector = bytes_per_vector
        self.bytes_per_label = bytes_per_label
        self.ef = ef
        self.update_single_neighbor = update_single_neighbor
        self.max_insert_iterations = max_insert_iterations
        self.max_query_iterations = max_query_iterations
        self.debugging_mode = debugging_mode

        self.nodes_capacity = 0
        self.data_capacity = 0

        self.max_data_blocks = 0
        self.max_node_blocks = 0

        self.cur_data_blocks = 0
        self.cur_node_blocks = 0

        self.num_nodes = 0
        self.num_data = 0

        self.max_entry = 100
        self.num_entry = 0
        self.num_count = 0

        self.entry_node = <coordi*> PyMem_Malloc(sizeof(coordi)*self.max_entry)
        self.cur_vec = <UCR*> PyMem_Malloc(sizeof(UCR)*self.bytes_per_vector)
        self.V = <Data**> PyMem_Malloc(sizeof(Data*)*search_v_max)
        self.C = <DataDist*> PyMem_Malloc(sizeof(DataDist)*search_c_max)
        self.W = <DataDist*> PyMem_Malloc(sizeof(DataDist)*self.ef*10)
        self.res = <coordi*> PyMem_Malloc(sizeof(coordi)*self.ef)
        self.res_query = <coordi*> PyMem_Malloc(sizeof(coordi)*self.ef*10)

        self.NULL_coordi.x = short_max
        self.NULL_coordi.y = short_max

        self.initialized = 0

    cpdef void index_trie(self, UCR*data, const UIDX num_total, UCR*all_ids, UCR*all_offsets, UCR*all_weights):
        cdef Node*node
        cdef UIDX _0
        cdef UST _1
        cdef UIDX _id
        cdef UST _offset
        cdef coordi parent_coordi

        if not self.initialized:
            self.all_nodes = <Node**> PyMem_Malloc(sizeof(Node*)*node_blocks_increment)
            self.all_data = <Data**> PyMem_Malloc(sizeof(Data*)*data_blocks_increment)
            self.all_neigh = <coordi**> PyMem_Malloc(sizeof(coordi*)*data_blocks_increment)

            block_nodes = <Node*> PyMem_Malloc(sizeof(Node)*node_size_per_time)
            block_data = <Data*> PyMem_Malloc(sizeof(Data)*data_size_per_time)
            block_neigh = <coordi*> PyMem_Malloc(sizeof(coordi)*data_size_per_time*self.ef*2)

            for _0 in range(data_size_per_time*self.ef*2):
                block_neigh[_0].x = self.NULL_coordi.x

            self.all_nodes[0] = block_nodes
            self.all_data[0] = block_data
            self.all_neigh[0] = block_neigh

            self.max_node_blocks = node_blocks_increment
            self.max_data_blocks = data_blocks_increment
            self.cur_node_blocks += 1
            self.cur_data_blocks += 1
            self.nodes_capacity += node_size_per_time
            self.data_capacity += data_size_per_time
            self.root_node = self.id2node(self.new_node(self.NULL_coordi))
            self.initialized = 1

        for _0 in range(num_total):
            node = self.root_node
            parent_coordi.x = 0
            parent_coordi.y = 0
            for _1 in range(self.bytes_per_vector):
                key = data[_1]
                self.cur_vec[_1] = key
                while True:
                    if node.key == 0 or node.key == key:
                        node.key = key
                        if node.child.x == self.NULL_coordi.x:
                            node.child = self.new_node(parent_coordi)
                            parent_coordi = node.child
                        parent_coordi = node.child
                        node = self.id2node(node.child)
                        break

                    elif key < node.key:
                        if node.left.x == self.NULL_coordi.x:
                            node.left = self.new_node(parent_coordi)
                            parent_coordi = node.left
                        parent_coordi = node.left
                        node = self.id2node(node.left)

                    elif key > node.key:
                        if node.right.x == self.NULL_coordi.x:
                            node.right = self.new_node(parent_coordi)
                            parent_coordi = node.right
                        parent_coordi = node.right
                        node = self.id2node(node.right)

            _id = bytes_to_label(all_ids, self.bytes_per_label)
            _offset = bytes_to_offset(all_offsets)
            _weight = bytes_to_offset(all_weights)
            self._index_value(node, parent_coordi, _id, _offset, _weight, self.cur_vec)
            data += self.bytes_per_vector
            all_ids += self.bytes_per_label
            all_offsets += 2
            all_weights += 2

    cdef coordi new_node(self, coordi parent_coordi):
        cdef Node*block_nodes
        cdef UIDX n_block
        cdef UIDX n_position
        cdef Node*node_next
        cdef coordi cur_coordi

        if self.num_nodes >= self.nodes_capacity:
            self.nodes_capacity += node_size_per_time
            block_nodes = <Node*> PyMem_Malloc(sizeof(Node)*node_size_per_time)
            n_block = int(self.nodes_capacity/node_size_per_time)
            # NOTE: judge here if need to update all nodes.
            if n_block > self.max_node_blocks:
                self.all_nodes = <Node**> PyMem_Realloc(
                    self.all_nodes,
                    sizeof(Node*)*(self.max_node_blocks+node_blocks_increment))
                self.max_node_blocks += node_blocks_increment

            # NOTE: then stick to the all nodes pointer list.
            self.all_nodes[n_block - 1] = block_nodes
            self.cur_node_blocks += 1

        cur_coordi.x = int(self.nodes_capacity / node_size_per_time) - 1
        cur_coordi.y = self.num_nodes + node_size_per_time - self.nodes_capacity
        node_next = self.id2node(cur_coordi)
        node_next.left = self.NULL_coordi
        node_next.right = self.NULL_coordi
        node_next.child = self.NULL_coordi
        node_next.key = 0
        node_next._next = self.NULL_coordi
        node_next.parent = parent_coordi
        self.num_nodes += 1
        return cur_coordi

    cdef void _index_value(self, Node*node, coordi parent_coordi, UIDX _id, UST _offset, UST _weight, UCR*cur_vec):
        cdef Data*data_block
        cdef Data*cur_node
        cdef coordi*neigh_block
        cdef coordi cur_coordi
        cdef UIDX n_block, n_position, _i

        # NOTE: upate data blocks and neighbor blocks
        if self.num_data >= self.data_capacity:
            self.data_capacity += data_size_per_time
            data_block = <Data*> PyMem_Malloc(sizeof(Data)*data_size_per_time)
            n_block = int(self.data_capacity / data_size_per_time)
            neigh_block = <coordi*> PyMem_Malloc(
                sizeof(coordi) * data_size_per_time * self.ef * 2)
            # NOTE: initialized all neighbors to NULL
            for _i in range(data_size_per_time*self.ef*2):
                neigh_block[_i] = self.NULL_coordi
            if n_block > self.max_data_blocks:
                self.all_data = <Data**>PyMem_Realloc(
                    self.all_data,
                    sizeof(Data*)*(self.max_data_blocks+data_blocks_increment))
                # NOTE: update neighbor pointers' size
                self.all_neigh = <coordi**>PyMem_Realloc(
                    self.all_neigh,
                    sizeof(coordi*)*(self.max_data_blocks+data_blocks_increment))
                # NOTE: update all_data size
                self.max_data_blocks += data_blocks_increment
            self.all_data[n_block - 1] = data_block
            self.all_neigh[n_block - 1] = neigh_block
            self.cur_data_blocks += 1

        # NOTE: update vector blocks
        n_block = int(self.data_capacity / data_size_per_time) - 1
        n_position = self.num_data + data_size_per_time - self.data_capacity

        cur_node = &self.all_data[n_block][n_position]
        cur_coordi.x = n_block
        cur_coordi.y = n_position
        cur_node.doc_id = _id
        cur_node.offset = _offset
        cur_node.weight = _weight
        cur_node._next.x = self.NULL_coordi.x
        cur_node._neighbor.x = n_block
        cur_node._neighbor.y = n_position * self.ef * 2
        cur_node.num_in = 0
        cur_node.parent = parent_coordi
        # NOTE: update vector in cur_node
        if node._next.x == self.NULL_coordi.x:
            node._next.x = n_block
            node._next.y = n_position
        else:
            new_node = self.id2data(node._next)
            while new_node._next.x != self.NULL_coordi.x:
                new_node = self.id2data(new_node._next)
            new_node._next.x = n_block
            new_node._next.y = n_position
        # NOTE: update cur_node neighbors, entry_points
        self.assign_neighbors(cur_node, cur_coordi)
        self.num_data += 1

    cdef void assign_neighbors(self, Data*cur_node, coordi cur_coordi):
        cdef UIDX _i, _j, _k, count, FLAG
        cdef coordi*res
        cdef Data*candi_node
        cdef UCR is_query
        cdef coordi neigh_coordi
        cdef UCR*_vec
        is_query = 0

        if self.num_data < self.ef:
            if self.num_data == 0:
                cur_node.num_out = 0
            for _i in range(self.num_data):
                self.all_neigh[cur_node._neighbor.x][cur_node._neighbor.y+_i].x = 0
                self.all_neigh[cur_node._neighbor.x][cur_node._neighbor.y+_i].y = _i
                cur_node.num_out = _i + 1
            if self.num_entry < 1:
                self.entry_node[self.num_entry] = cur_coordi
                self.num_entry += 1
        else:
            _vec = self.node2vec(cur_node)
            res = self.search_neighbors(_vec, is_query)
            PyMem_Free(_vec)
            for _i in range(self.ef):
                if res[_i].x != self.NULL_coordi.x:
                    self.all_neigh[cur_node._neighbor.x][cur_node._neighbor.y+_i] = res[_i]
                    cur_node.num_out = _i + 1
                else:
                    break
        # NOTE: add bidirectional connections.
        for _k in range(cur_node.num_out):
            neigh_coordi = self.all_neigh[cur_node._neighbor.x][cur_node._neighbor.y+_k]
            self.update_neighbors(cur_coordi, neigh_coordi)

    cdef coordi*search_neighbors(self, UCR*cur_vec, UCR is_query):
        '''
            V: visited node list
            C: candidate node list
            W: selected node list
            res: return list

        '''
        cdef Data*candi_node, *entry_node
        cdef DataDist c_near, w_far, w_far_new
        cdef UST v_len=0, c_len, w_len
        cdef UIDX i, j, k, max_iterations
        cdef UCR FLAG
        cdef UST eq_dist, max_dist_w, min_dist_c
        cdef coordi*res
        cdef coordi cur_coordi
        cdef UCR*_vec

        # NOTE: get the farest node in W and nearest node in C
        if is_query:
            max_iterations = self.max_query_iterations
        else:
            max_iterations = self.max_insert_iterations
        max_dist_w = 0
        min_dist_c = self.bytes_per_vector + 1
        for i in range(self.num_entry):
            entry_node = self.id2data(self.entry_node[i])
            _vec = self.node2vec(entry_node)
            eq_dist = vec_distance(_vec, cur_vec, self.bytes_per_vector)
            PyMem_Free(_vec)
            self.C[i].dist = eq_dist
            self.C[i].data = entry_node
            self.C[i].data_coordi = self.entry_node[i]
            if i < self.ef * 10:
                self.W[i].dist = eq_dist
                self.W[i].data = entry_node
                self.W[i].data_coordi = self.entry_node[i]

            self.V[i] = entry_node
            v_len += 1

        # v_len = 0
        c_len = min(self.num_entry, self.ef*10)
        w_len = min(self.num_entry, self.ef*10)
        cdef int count
        count = 0

        while c_len > 0:
            max_dist_w = 0
            min_dist_c = self.bytes_per_vector + 1
            for i in range(w_len):
                if self.W[i].dist > max_dist_w:
                    max_dist_w = self.W[i].dist
                    w_far = self.W[i]
            for i in range(c_len):
                if self.C[i].dist < min_dist_c:
                    min_dist_c = self.C[i].dist
                    c_near = self.C[i]
            if (count > max_iterations) or (c_near.dist > w_far.dist):
                self.num_count += 1
                break

            if v_len < search_v_max:
                self.V[v_len] = c_near.data
                v_len += 1

            for i in range(c_near.data.num_out):
                cur_coordi = self.all_neigh[c_near.data._neighbor.x][c_near.data._neighbor.y+i]
                candi_node = self.id2data(cur_coordi)
                FLAG = 1
                # NOTE: check if candi_node in V
                # NOTE: check if candi_node in W already
                for j in range(v_len):
                    if candi_node == self.V[j]:
                        FLAG = 0
                        break
                for j in range(w_len):
                    if candi_node == self.W[j].data:
                        FLAG = 0
                        break
                if FLAG:
                    if v_len < search_v_max:
                        self.V[v_len] = candi_node
                        v_len += 1
                    else:
                        print('visisted list is full ...')
                    _vec = self.node2vec(candi_node)
                    eq_dist = vec_distance(_vec, cur_vec, self.bytes_per_vector)
                    PyMem_Free(_vec)
                    count += 1
                    if w_len < self.ef * 10:
                        self.W[w_len].data = candi_node
                        self.W[w_len].dist = eq_dist
                        self.W[w_len].data_coordi = cur_coordi
                        if max_dist_w < eq_dist:
                            max_dist_w = eq_dist
                            w_far = self.W[w_len]

                        w_len += 1
                        # NOTE: insrt this node into C
                        if c_len < search_c_max:
                            self.C[c_len].data = candi_node
                            self.C[c_len].dist = eq_dist
                            self.C[c_len].data_coordi = cur_coordi
                            c_len += 1

                    elif eq_dist < w_far.dist:
                        # NOTE: insrt this node into W
                        max_dist_w = 0
                        for k in range(w_len):
                            if self.W[k].data == w_far.data:
                                self.W[k].data = candi_node
                                self.W[k].dist = eq_dist
                                self.W[k].data_coordi = cur_coordi
                            if self.W[k].dist > max_dist_w:
                                max_dist_w = self.W[k].dist
                                w_far_new = self.W[k]
                        w_far = w_far_new

                        # NOTE: insrt this node into C
                        if c_len < search_c_max:
                            self.C[c_len].data = candi_node
                            self.C[c_len].dist = eq_dist
                            self.C[c_len].data_coordi = cur_coordi
                            c_len += 1

            # extract c_near
            for i in range(c_len):
                if self.C[i].data == c_near.data:
                    self.C[i] = self.C[c_len-1]
                    break
            c_len -= 1

        sort_Datadist(self.W, w_len)
        if is_query:
            for i in range(self.ef*10):
                if i < w_len:
                    self.res_query[i] = self.W[i].data_coordi
                else:
                    self.res_query[i] = self.NULL_coordi
            res = self.res_query
        else:
            for i in range(self.ef):
                if i < w_len:
                    self.res[i] = self.W[i].data_coordi
                else:
                    self.res[i] = self.NULL_coordi
            res = self.res
        return res

    cdef void update_neighbors(self, coordi cur_coordi, coordi neigh_coordi):
        cdef UST cur_dist, max_dist
        cdef UST i, replace, dist
        cdef Data*org_node, *update_node
        cdef coordi tmp_coordi
        cdef UCR*_vec1, *_vec2
        cdef UST FLAG, _x
        cdef UIDX _y
        org_node = self.id2data(cur_coordi)
        update_node= self.id2data(neigh_coordi)

        max_dist = 0
        FLAG = 1
        if update_node.num_out < self.ef * 2:
            for i in range(update_node.num_out):
                tmp_coordi = self.all_neigh[update_node._neighbor.x][update_node._neighbor.y+i]
                if (tmp_coordi.x == cur_coordi.x) and (tmp_coordi.y == cur_coordi.y):
                    FLAG = 0
                    break
            if FLAG:
                _x = update_node._neighbor.x
                _y = update_node._neighbor.y + update_node.num_out
                self.all_neigh[_x][_y] = cur_coordi
                update_node.num_out += 1
        else:
            _vec1 = self.node2vec(org_node)
            _vec2 = self.node2vec(update_node)
            dist = vec_distance(_vec1, _vec2, self.bytes_per_vector)
            PyMem_Free(_vec1)
            PyMem_Free(_vec2)
            if self.update_single_neighbor:
                max_dist = 0
                for i in range(update_node.num_out):
                    _x = update_node._neighbor.x
                    _y = update_node._neighbor.y + i
                    tmp_coordi = self.all_neigh[_x][_y]
                    _vec1 = self.id2vec(tmp_coordi)
                    _vec2 = self.node2vec(update_node)
                    cur_dist = vec_distance(_vec1, _vec2, self.bytes_per_vector)
                    PyMem_Free(_vec1)
                    PyMem_Free(_vec2)
                    if cur_dist > max_dist:
                        max_dist = cur_dist
                        replace = i
                if max_dist > dist:
                    _x = update_node._neighbor.x
                    _y = update_node._neighbor.y + replace
                    self.all_neigh[_x][_y] = cur_coordi
            else:
                neighbor = <DataDist*> PyMem_Malloc(sizeof(DataDist)*update_node.num_out)
                for i in range(update_node.num_out):
                    _x = update_node._neighbor.x
                    _y = update_node._neighbor.y + i
                    tmp_coordi = self.all_neigh[_x][_y]
                    _vec1 = self.id2vec(tmp_coordi)
                    _vec2 = self.node2vec(update_node)
                    cur_dist = vec_distance(_vec1, _vec2, self.bytes_per_vector)
                    PyMem_Free(_vec1)
                    PyMem_Free(_vec2)
                    neighbor[i].data = self.id2data(tmp_coordi)
                    neighbor[i].dist = cur_dist
                    neighbor[i].data_coordi = tmp_coordi
                sort_Datadist(neighbor, update_node.num_out)
                for i in range(self.ef):
                    _x = update_node._neighbor.x
                    _y = update_node._neighbor.y + i
                    self.all_neigh[_x][_y] = neighbor[i].data_coordi
                if dist < neighbor[self.ef-1].dist:
                    _x = update_node._neighbor.x
                    _y = update_node._neighbor.y + self.ef - 1
                    self.all_neigh[_x][_y] = cur_coordi
                update_node.num_out = self.ef
                PyMem_Free(neighbor)

    cpdef find_batch_trie(self, unsigned char*query, const UIDX num_query):
        cdef array.array final_result = array.array('L')
        cdef array.array final_offset = array.array('L')
        cdef array.array final_weight = array.array('L')
        cdef array.array final_idx = array.array('L')
        cdef Node*node
        cdef Data*dnode
        cdef unsigned char*q_pt
        cdef UIDX _0
        cdef UST _1
        cdef UCR is_match
        q_pt = query

        for _0 in range(num_query):
            node = self.root_node
            is_match = 1
            for _1 in range(self.bytes_per_vector):
                key = q_pt[_1]
                while node:
                    if node.key == key:
                        if node.child.x == self.NULL_coordi.x:
                            is_match = 0
                            break
                        else:
                            node = self.id2node(node.child)
                            break
                    elif key < node.key:
                        if node.left.x == self.NULL_coordi.x:
                            is_match = 0
                            break
                        else:
                            node = self.id2node(node.left)
                    elif key > node.key:
                        if node.right.x == self.NULL_coordi.x:
                            is_match = 0
                            break
                        else:
                            node = self.id2node(node.right)
                if not node:
                    is_match = 0
                if is_match == 0:
                    break
            if is_match == 1 and (node._next.x != self.NULL_coordi.x):
                dnode = self.id2data(node._next)
                final_result.append(dnode.doc_id)
                final_offset.append(dnode.offset)
                final_weight.append(dnode.weight)
                final_idx.append(_0)
                while dnode._next.x != self.NULL_coordi.x:
                    dnode = self.id2data(dnode._next)
                    final_result.append(dnode.doc_id)
                    final_offset.append(dnode.offset)
                    final_weight.append(dnode.weight)
                    final_idx.append(_0)

            q_pt += self.bytes_per_vector
        return final_idx, final_result, final_offset, final_weight

    cpdef nsw_search(self, unsigned char*query, const UIDX num_query, const UIDX top_k):
        cdef array.array res_dist = array.array('L')
        cdef array.array res_docs = array.array('L')
        cdef array.array res_offset = array.array('L')
        cdef array.array res_weight = array.array('L')
        cdef array.array res_idx = array.array('L')

        cdef coordi*res
        cdef UIDX _0
        cdef UST _1
        cdef UCR is_query
        is_query = 1
        for _0 in range(num_query):
            for _1 in range(self.bytes_per_vector):
                self.cur_vec[_1] = query[_1]
            query += self.bytes_per_vector
            res = self.search_neighbors(self.cur_vec, is_query)
            for _1 in range(top_k):
                if res[_1].x != self.NULL_coordi.x:
                    res_idx.append(_0)
                    res_docs.append(self.id2data(res[_1]).doc_id)
                    res_offset.append(self.id2data(res[_1]).offset)
                    res_weight.append(self.id2data(res[_1]).weight)
                    res_dist.append(vec_distance(self.cur_vec, self.id2vec(res[_1]), self.bytes_per_vector))
                else:
                    break

        return res_docs, res_offset, res_weight, res_dist, res_idx

    cpdef force_search(self, unsigned char*query, const UIDX num_query, UIDX top_k):
        cdef array.array res_dist = array.array('L')
        cdef array.array res_docs = array.array('L')
        cdef array.array res_offset = array.array('L')
        cdef array.array res_weight = array.array('L')
        cdef array.array res_idx = array.array('L')
        cdef DataDist w_far
        top_k = min(top_k, self.num_data)

        cdef coordi tmp
        cdef UCR*tmp_vec
        cdef UIDX _0, _1, _2, _3, _id, _dist, _dist_far

        for _0 in range(num_query):
            Q = <DataDist*> PyMem_Malloc(sizeof(DataDist) * top_k)
            w_far.dist = 0
            for _1 in range(self.bytes_per_vector):
                self.cur_vec[_1] = query[_1]
            query += self.bytes_per_vector
            for _2 in range(self.cur_data_blocks):
                for _3 in range(data_size_per_time):
                    _id = _2 * data_size_per_time + _3
                    if _id < self.num_data:
                        tmp.x = _2
                        tmp.y = _3
                        tmp_vec = self.id2vec(tmp)
                        if _id < top_k:
                            Q[_id].data_coordi = tmp
                            Q[_id].dist = vec_distance(self.id2vec(tmp), self.cur_vec, self.bytes_per_vector)
                            Q[_id].data = &self.all_data[_2][_3]
                            if Q[_id].dist > w_far.dist:
                                w_far = Q[_id]
                        else:
                            _dist = vec_distance(self.id2vec(tmp), self.cur_vec, self.bytes_per_vector)
                            if _dist < w_far.dist:
                                _dist_far = 0
                                for _1 in range(top_k):
                                    if Q[_1].data == w_far.data:
                                        Q[_1].data = &self.all_data[_2][_3]
                                        Q[_1].data_coordi = tmp
                                        Q[_1].dist = _dist
                                        break
                                for _1 in range(top_k):
                                    if Q[_1].dist > _dist_far:
                                        _dist_far = Q[_1].dist
                                        w_far = Q[_1]
            sort_Datadist(Q, top_k)
            for _1 in range(top_k):
                res_idx.append(_0)
                res_docs.append(Q[_1].data.doc_id)
                res_offset.append(Q[_1].data.offset)
                res_weight.append(Q[_1].data.weight)
                res_dist.append(Q[_1].dist)
            PyMem_Free(Q)

        return res_docs, res_offset, res_weight, res_dist, res_idx

    def __dealloc__(self):
        self.free_trie()

    cdef Data*id2data(self, coordi data_coordi):
        return &self.all_data[data_coordi.x][data_coordi.y]

    cdef Node*id2node(self, coordi node_coordi):
        return &self.all_nodes[node_coordi.x][node_coordi.y]

    cdef UCR*id2vec(self, coordi data_coordi):
        return self.node2vec(self.id2data(data_coordi))

    cdef UCR*node2vec(self, Data*data):
        cdef Node*node
        cdef Node*node_before
        cdef int i
        cur_vec = <UCR*> PyMem_Malloc(sizeof(UCR)*self.bytes_per_vector)
        node = self.id2node(data.parent)

        i = self.bytes_per_vector-1

        while i >= 0:
            if node.parent.x != self.NULL_coordi.x:
                node_before = node
                node = self.id2node(node_before.parent)
                if self.id2node(node.child) == node_before:
                    cur_vec[i] = node.key
                    i -= 1
            else:
                cur_vec[i] = self.root_node.key
                i -= 1
        return cur_vec

    cdef void _save(self, char*save_path):
        cdef FILE*save_file
        cdef UIDX i
        save_file = fopen(save_path, "wb")
        # NOTE: write cur_data_blocks, cur_node_blocks
        fwrite(&self.cur_data_blocks, sizeof(UIDX), 1, save_file)
        fwrite(&self.cur_node_blocks, sizeof(UIDX), 1, save_file)
        fwrite(&self.num_data, sizeof(UIDX), 1, save_file)
        fwrite(&self.num_nodes, sizeof(UIDX), 1, save_file)
        fwrite(&self.num_entry, sizeof(UST), 1, save_file)
        fwrite(&self.max_data_blocks, sizeof(UIDX), 1, save_file)
        fwrite(&self.max_node_blocks, sizeof(UIDX), 1, save_file)
        fwrite(&self.data_capacity, sizeof(UIDX), 1, save_file)
        fwrite(&self.nodes_capacity, sizeof(UIDX), 1, save_file)
        fwrite(self.entry_node, sizeof(coordi), self.max_entry, save_file)
        for i in range(self.cur_data_blocks):
            fwrite(self.all_data[i], sizeof(Data), data_size_per_time, save_file)
        for i in range(self.cur_node_blocks):
            fwrite(self.all_nodes[i], sizeof(Node), node_size_per_time, save_file)
        for i in range(self.cur_data_blocks):
            fwrite(self.all_neigh[i], sizeof(coordi), data_size_per_time*self.ef*2, save_file)
        fclose(save_file)

    cdef void _load(self, char*load_path):
        cdef FILE*load_file
        cdef UIDX i
        load_file = fopen(load_path, "rb")
        fread(&self.cur_data_blocks, sizeof(UIDX), 1, load_file)
        fread(&self.cur_node_blocks, sizeof(UIDX), 1, load_file)
        fread(&self.num_data, sizeof(UIDX), 1, load_file)
        fread(&self.num_nodes, sizeof(UIDX), 1, load_file)
        fread(&self.num_entry, sizeof(UST), 1, load_file)
        fread(&self.max_data_blocks, sizeof(UIDX), 1, load_file)
        fread(&self.max_node_blocks, sizeof(UIDX), 1, load_file)
        fread(&self.data_capacity, sizeof(UIDX), 1, load_file)
        fread(&self.nodes_capacity, sizeof(UIDX), 1, load_file)
        fread(self.entry_node, sizeof(coordi), self.max_entry, load_file)
        self.all_nodes = <Node**> PyMem_Malloc(sizeof(Node*)*self.max_node_blocks)
        self.all_data = <Data**> PyMem_Malloc(sizeof(Data*)*self.max_data_blocks)
        self.all_neigh = <coordi**> PyMem_Malloc(sizeof(coordi*)*self.max_data_blocks)
        self.initialized = 1

        for i in range(self.cur_data_blocks):
            block_data = <Data*> PyMem_Malloc(sizeof(Data)*data_size_per_time)
            fread(block_data, sizeof(Data), data_size_per_time, load_file)
            self.all_data[i] = block_data
        for i in range(self.cur_node_blocks):
            block_nodes = <Node*> PyMem_Malloc(sizeof(Node)*node_size_per_time)
            fread(block_nodes, sizeof(Node), node_size_per_time, load_file)
            self.all_nodes[i] = block_nodes
        for i in range(self.cur_data_blocks):
            block_neigh = <coordi*> PyMem_Malloc(sizeof(coordi)*data_size_per_time*self.ef*2)
            fread(block_neigh, sizeof(coordi), data_size_per_time*self.ef*2, load_file)
            self.all_neigh[i] = block_neigh

        self.root_node = &self.all_nodes[0][0]
        fclose(load_file)

    def save(self, save_path):
        self._save(bytes(save_path, 'utf8'))

    def load(self, load_path):
        self._load(bytes(load_path, 'utf8'))

    cdef vec_distance(self, UCR*va, UCR*vb):
        cdef UST i, dist
        dist = 0
        for i in range(self.bytes_per_vector):
            if va[i] != vb[i]:
                dist += 1
        return dist

    def debugging(self):
        for i in range(self.num_data-10, self.num_data):
            x = int(i / data_size_per_time)
            y = i - x * data_size_per_time

            print(self.all_data[x][y].doc_id, self.all_neigh[x][y*self.ef*2+1].x, self.all_neigh[x][y*self.ef*2+1].y)

        for i in range(self.num_data-3, self.num_data):
            res = []
            vec = self.node2vec(&self.all_data[0][i])
            for j in range(self.bytes_per_vector):
                res.append(vec[j])
            print(res)
        print('-'*100)
        for i in range(self.num_data-10, self.num_data):
            x = self.all_data[0][i].parent.x
            y = self.all_data[0][i].parent.y
            print(x, y, self.all_nodes[x][y].key)

    def destroy(self):
        self.free_trie()

    cdef void free_trie(self):
        cdef UIDX _
        PyMem_Free(self.V)
        PyMem_Free(self.W)
        PyMem_Free(self.C)
        PyMem_Free(self.res)
        PyMem_Free(self.res_query)
        PyMem_Free(self.entry_node)
        PyMem_Free(self.cur_vec)
        for _ in range(int(self.nodes_capacity/node_size_per_time)):
            PyMem_Free(self.all_nodes[_])
        for _ in range(int(self.data_capacity/data_size_per_time)):
            PyMem_Free(self.all_neigh[_])
        for _ in range(int(self.data_capacity/data_size_per_time)):
            PyMem_Free(self.all_data[_])
        PyMem_Free(self.all_neigh)
        PyMem_Free(self.all_nodes)
        PyMem_Free(self.all_data)