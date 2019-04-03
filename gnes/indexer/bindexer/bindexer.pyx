# cython: language_level=3, wraparound=False, boundscheck=False
# noinspection PyUnresolvedReferences
# created 2019-03-27

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from cpython cimport array
from libc.stdlib cimport qsort
import random
import math

DEF data_size_per_time = 100000
DEF node_size_per_time = 100000
DEF data_blocks_increment = 100
DEF node_blocks_increment = 100

DEF search_v_max = 10000
DEF search_c_max = 10000
DEF search_w_max = 10000

ctypedef unsigned int UIDX
ctypedef unsigned short UST
ctypedef unsigned char UCR

cdef struct Node:
    Node*left
    Node*right
    Node*child
    unsigned char key
    Data*_next

cdef struct Data:
    UIDX doc_id
    Data*_next
    Data**_neighbor
    UST num_in
    UST num_out
    UCR*vector

cdef struct DataDist:
    Data*data
    UST dist

cdef UIDX bytes_to_label(UCR*all_ids, UST bytes_per_label):
    cdef UIDX label
    cdef UST _
    label = 0
    for _ in range(bytes_per_label):
        label += (256**_) * all_ids[_]
    return label

cdef int cmpfunc(const void*a, const void*b) nogil:
    cdef DataDist*av = <DataDist*>a
    cdef DataDist*bv = <DataDist*>b
    return av.dist - bv.dist

cdef DataDist*sort_Datadist(DataDist*W, UIDX wsize):
    qsort(W, wsize, sizeof(DataDist), &cmpfunc)
    return W

cdef class IndexCore:
    cdef Node*root_node
    cdef UST bytes_per_vector
    cdef UST bytes_per_label
    cdef UST ef
    cdef UIDX max_insert_iterations
    cdef UIDX max_query_iterations

    cdef Data**all_data
    cdef Node**all_nodes
    cdef Data***all_neigh
    cdef UCR**all_bytes
    cdef Data**entry_node

    cdef UIDX nodes_capacity
    cdef UIDX data_capacity
    cdef UIDX vec_capacity

    cdef UIDX max_data_blocks
    cdef UIDX max_node_blocks
    cdef UIDX max_vec_blocks

    cdef UIDX num_nodes
    cdef UIDX num_data
    cdef UIDX uniq_data
    cdef UST num_entry
    cdef UST num_count
    cdef UST max_entry

    cdef UCR*cur_vec
    cdef DataDist*W
    cdef DataDist*C
    cdef Data**V
    cdef Data**res
    cdef UCR update_single_neighbor, debugging_mode

    cpdef void index_trie(self, UCR*data, const UIDX num_total, UCR*all_ids):
        cdef Node*node
        cdef UIDX _0
        cdef UST _1
        cdef UIDX _id

        if not self.root_node:
            self.all_nodes = <Node**> PyMem_Malloc(sizeof(Node*)*node_blocks_increment)
            self.all_data = <Data**> PyMem_Malloc(sizeof(Data*)*data_blocks_increment)
            self.all_neigh = <Data***> PyMem_Malloc(sizeof(Data**)*data_blocks_increment)
            self.all_bytes = <UCR**> PyMem_Malloc(sizeof(UCR*)*data_blocks_increment)

            block_nodes = <Node*> PyMem_Malloc(sizeof(Node)*node_size_per_time)
            block_data = <Data*> PyMem_Malloc(sizeof(Data)*data_size_per_time)
            block_neigh = <Data**> PyMem_Malloc(sizeof(Data*)*data_size_per_time*self.ef*2)
            block_bytes = <UCR*> PyMem_Malloc(sizeof(UCR)*data_size_per_time*self.bytes_per_vector)

            self.cur_vec = <UCR*> PyMem_Malloc(sizeof(UCR)*self.bytes_per_vector)
            self.V = <Data**> PyMem_Malloc(sizeof(Data*)*search_v_max)
            self.C = <DataDist*> PyMem_Malloc(sizeof(DataDist)*search_c_max)
            self.W = <DataDist*> PyMem_Malloc(sizeof(DataDist)*self.ef*10)
            self.res = <Data**> PyMem_Malloc(sizeof(Data*)*self.ef)

            for _0 in range(data_size_per_time*self.ef*2):
                block_neigh[_0] = NULL

            self.max_node_blocks = node_blocks_increment
            self.max_data_blocks = data_blocks_increment
            self.max_vec_blocks = data_blocks_increment

            self.all_nodes[0] = block_nodes
            self.all_data[0] = block_data
            self.all_neigh[0] = block_neigh
            self.all_bytes[0] = block_bytes

            self.nodes_capacity = node_size_per_time
            self.data_capacity = data_size_per_time
            self.vec_capacity = data_size_per_time
            self.num_nodes = 0
            self.num_data = 0
            self.uniq_data = 0
            self.root_node = self.new_node()
            self.max_entry = 100
            self.entry_node = <Data**> PyMem_Malloc(sizeof(Data*)*self.max_entry)
            self.num_entry = 0
            self.num_count = 0

        for _0 in range(num_total):
            node = self.root_node
            for _1 in range(self.bytes_per_vector):
                key = data[_1]
                self.cur_vec[_1] = key
                while True:
                    if node.key == 0 or node.key == key:
                        node.key = key
                        if node.child == NULL:
                            node.child = self.new_node()
                        node = node.child
                        break
                    elif key < node.key:
                        if node.left == NULL:
                            node.left = self.new_node()
                        node = node.left
                    elif key > node.key:
                        if node.right == NULL:
                            node.right = self.new_node()
                        node = node.right
            _id = bytes_to_label(all_ids, self.bytes_per_label)
            self._index_value(node, _id, self.cur_vec)
            data += self.bytes_per_vector
            all_ids += self.bytes_per_label

    cdef Node*new_node(self):
        cdef Node* r
        cdef int flag
        cdef UIDX n_block
        cdef UIDX n_position

        if self.num_nodes >= self.nodes_capacity:
            self.nodes_capacity += node_size_per_time
            r = <Node*> PyMem_Malloc(sizeof(Node)*node_size_per_time)
            n_block = int(self.nodes_capacity/node_size_per_time)
            # judge here if need to update all nodes.
            if n_block > self.max_node_blocks:
                self.all_nodes = <Node**> PyMem_Realloc(
                    self.all_nodes,
                    sizeof(Node*)*(self.max_node_blocks+node_blocks_increment))
                self.max_node_blocks += node_blocks_increment
            # then stick to the all nodes pointer list.
            self.all_nodes[n_block - 1] = r

        n_block = int(self.nodes_capacity / node_size_per_time) - 1
        n_position = self.num_nodes + node_size_per_time - self.nodes_capacity
        cdef Node* node_next
        node_next = &self.all_nodes[n_block][n_position]
        node_next.left = NULL
        node_next.right = NULL
        node_next.child = NULL
        node_next.key = 0
        node_next._next = NULL
        self.num_nodes += 1
        return node_next

    cpdef find_batch_trie(self, unsigned char*query, const UIDX num_query):
        cdef array.array final_result = array.array('L')
        cdef array.array final_idx = array.array('L')
        cdef Node*node
        cdef Data*dnode
        cdef unsigned char *q_pt
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
                        if not node.child:
                            is_match = 0
                            break
                        else:
                            node = node.child
                            break
                    elif key < node.key:
                        if not node.left:
                            is_match = 0
                            break
                        else:
                            node = node.left
                    elif key > node.key:
                        if not node.right:
                            is_match = 0
                            break
                        else:
                            node = node.right
                if not node:
                    is_match = 0
                if is_match == 0:
                    break
            if is_match == 1 and (node._next != NULL):
                dnode = node._next
                final_result.append(dnode.doc_id)
                final_idx.append(_0)
                while dnode._next != NULL:
                    dnode = dnode._next
                    final_result.append(dnode.doc_id)
                    final_idx.append(_0)

            q_pt += self.bytes_per_vector
        return final_idx, final_result

    cpdef nsw_search(self, unsigned char*query, const UIDX num_query):
        cdef array.array res_dist = array.array('L')
        cdef array.array res_docs = array.array('L')
        cdef array.array res_idx = array.array('L')

        cdef Data**res
        cdef UIDX _0
        cdef UST _1
        cdef UCR is_query
        is_query = 1
        for _0 in range(num_query):
            for _1 in range(self.bytes_per_vector):
                self.cur_vec[_1] = query[_1]
            query += self.bytes_per_vector
            res = self.search_neighbors(self.cur_vec, is_query)
            for _1 in range(self.ef):
                if res[_1] != NULL:
                    res_idx.append(_0)
                    res_docs.append(res[_1].doc_id)
                    res_dist.append(self.vec_distance(self.cur_vec, res[_1].vector))

        return res_docs, res_dist, res_idx

    cdef void _index_value(self, Node*node, UIDX _id, UCR*cur_vec):
        cdef Data*data_block
        cdef Data*cur_node
        cdef UCR*vec_block
        cdef Data**neigh_block
        cdef UIDX n_block, n_position, _i

        # NOTE: upate data blocks and neighbor blocks
        if self.num_data >= self.data_capacity:
            self.data_capacity += data_size_per_time
            data_block = <Data*> PyMem_Malloc(sizeof(Data)*data_size_per_time)
            n_block = int(self.data_capacity / data_size_per_time)
            neigh_block = <Data**> PyMem_Malloc(
                            sizeof(Data*) * data_size_per_time * self.ef * 2)
            # NOTE: initialized all neighbors to NULL
            for _i in range(data_size_per_time*self.ef*2):
                neigh_block[_i] = NULL
            if n_block > self.max_data_blocks:
                self.all_data = <Data**>PyMem_Realloc(
                    self.all_data,
                    sizeof(Data*)*(self.max_data_blocks+data_blocks_increment))
                # NOTE: update neighbor pointers' size
                self.all_neigh = <Data***>PyMem_Realloc(
                    self.all_neigh,
                    sizeof(Data**)*(self.max_data_blocks+data_blocks_increment))
                # NOTE: update all_data size
                self.max_data_blocks += data_blocks_increment
            self.all_data[n_block - 1] = data_block
            self.all_neigh[n_block - 1] = neigh_block
        # NOTE: update vector blocks if it's full.
        if self.uniq_data >= self.vec_capacity:
            self.vec_capacity += data_size_per_time
            vec_block = <UCR*> PyMem_Malloc(sizeof(UCR)*data_size_per_time*self.bytes_per_vector)
            v_block = int(self.vec_capacity / data_size_per_time)
            if v_block > self.max_vec_blocks:
                self.all_bytes = <UCR**> PyMem_Realloc(
                    self.all_bytes,
                    sizeof(UCR*)*(self.max_vec_blocks+data_blocks_increment))
                self.max_vec_blocks += data_blocks_increment
            self.all_bytes[v_block - 1] = vec_block
        # NOTE: update vector blocks
        n_block = int(self.data_capacity / data_size_per_time) - 1
        n_position = self.num_data + data_size_per_time - self.data_capacity

        cur_node = &self.all_data[n_block][n_position]
        cur_node.doc_id = _id
        cur_node._next = NULL
        cur_node._neighbor = &self.all_neigh[n_block][n_position*self.ef*2]
        cur_node.num_in = 0
        # NOTE: update vector in cur_node
        if node._next == NULL:
            n_block = int(self.vec_capacity / data_size_per_time) - 1
            n_position = (self.uniq_data + data_size_per_time
                          - self.vec_capacity) * self.bytes_per_vector
            for i in range(self.bytes_per_vector):
                self.all_bytes[n_block][n_position + i] = cur_vec[i]
            self.uniq_data += 1
            cur_node.vector = &self.all_bytes[n_block][n_position]
            node._next = cur_node
        else:
            new_node = node._next
            while new_node._next != NULL:
                new_node = new_node._next
            cur_node.vector = new_node.vector
            new_node._next = cur_node
        # NOTE: update cur_node neighbors, entry_points
        self.assign_neighbors(cur_node)
        self.num_data += 1

    cdef UST assign_neighbors(self, Data*cur_node):
        cdef UIDX _i, _j, _k, count, FLAG
        cdef Data**res
        cdef Data*candi_node
        cdef UCR is_query
        is_query = 0

        if self.num_data < self.ef:
            if self.num_data == 0:
                cur_node.num_out = 0
            for _i in range(self.num_data):
                cur_node._neighbor[_i] = &self.all_data[0][_i]
                cur_node.num_out = _i + 1
            if self.num_entry < 1:
                self.entry_node[self.num_entry] = cur_node
                self.num_entry += 1
        else:
            if random.uniform(0, 1) >= 0.0:
                res = self.search_neighbors(cur_node.vector, is_query)
            else:
                res = self.search_neighbors_force(cur_node.vector)
            for i in range(self.ef):
                if res[i] != NULL:
                    if res[i].doc_id != cur_node.doc_id:
                        cur_node._neighbor[i] = res[i]
                    else:
                        cur_node._neighbor[i] = self.random_neighbors(cur_node.doc_id)
                    cur_node.num_out = i + 1
                else:
                    break
        # NOTE: add bidirectional connections.
        for _k in range(cur_node.num_out):
            self.update_neighbors(cur_node, cur_node._neighbor[_k])

    cdef Data*random_neighbors(self, UIDX doc_id):
        cdef UIDX i, n_block, n_position
        cdef Data*random_node
        i = random.randint(0, self.num_data-1)

        n_block = int(i / data_size_per_time)
        n_position = i - n_block * data_size_per_time
        random_node = &self.all_data[n_block][n_position]
        if random_node.doc_id != doc_id:
            return random_node
        else:
            return self.random_neighbors(doc_id)

    cdef void update_neighbors(self, Data*org_node, Data*update_node):
        cdef UST cur_dist, max_dist
        cdef UST i, replace, dist
        cdef Data**res
        cdef Data*tmp
        cdef UST FLAG

        max_dist = 0
        FLAG = 1
        if update_node.num_out < self.ef * 2:
            for i in range(update_node.num_out):
                if update_node._neighbor[i] == org_node:
                    FLAG = 0
                    break
            if FLAG:
                update_node._neighbor[update_node.num_out] = org_node
                update_node.num_out += 1
        else:
            dist = self.vec_distance(org_node.vector, update_node.vector)
            if self.update_single_neighbor:
                max_dist = 0
                for i in range(update_node.num_out):
                    cur_dist = self.vec_distance(
                        update_node._neighbor[i].vector, update_node.vector)
                    if cur_dist > max_dist:
                        max_dist = cur_dist
                        replace = i
                if max_dist > dist:
                    update_node._neighbor[replace] = org_node
            else:
                neighbor = <DataDist*> PyMem_Malloc(sizeof(DataDist)*update_node.num_out)
                for i in range(update_node.num_out):
                    cur_dist = self.vec_distance(
                        update_node._neighbor[i].vector, update_node.vector)
                    neighbor[i].data = update_node._neighbor[i]
                    neighbor[i].dist = cur_dist
                sort_Datadist(neighbor, update_node.num_out)
                for i in range(self.ef):
                    update_node._neighbor[i] = neighbor[i].data
                if dist < neighbor[self.ef-1].dist:
                    update_node._neighbor[self.ef-1] = org_node
                update_node.num_out = self.ef
                PyMem_Free(neighbor)

    cdef Data**search_neighbors_force(self, UCR*cur_vec):
        cdef UST _k, _j, _nrow, _ncol, _max_dist
        cdef UIDX _i
        cdef DataDist v
        cdef DataDist v_max
        cdef Data*cur_node
        cdef Data**res

        _k = 0
        v_max.dist = 0
        for _i in range(self.num_data):
            _nrow = int(_i / data_size_per_time)
            _ncol = _i - data_size_per_time * _nrow

            cur_node = &self.all_data[_nrow][_ncol]
            dist = self.vec_distance(cur_vec, cur_node.vector)
            if _k < self.ef:
                self.W[_k].dist = dist
                self.W[_k].data = cur_node
                _k += 1
                if dist > v_max.dist:
                    v_max = self.W[_k]
            # NOTE: update if distance less than max(neighbor dist)
            elif dist < v_max.dist:
                for _j in range(self.ef):
                    if self.W[_j].data == v_max.data:
                        self.W[_j].data = cur_node
                        self.W[_j].dist = dist
                        break
                # NOTE: update the max(neigbor dist)
                v_max.dist = 0
                for _j in range(self.ef):
                    if self.W[_j].dist > v_max.dist:
                        v_max = self.W[_j]

        for _i in range(self.ef):
            self.res[_i] = self.W[_i].data

        res = self.res
        return res

    cdef Data**search_neighbors(self, UCR*cur_vec, UCR is_query):
        '''
            V: visited node list
            C: candidate node list
            W: selected node list
            res: return list

        '''
        cdef Data*candi_node
        cdef DataDist c_near, w_far, w_far_new
        cdef UST v_len=0, c_len, w_len
        cdef UIDX i, j, k, max_iterations
        cdef UCR FLAG
        cdef UST eq_dist, max_dist_w, min_dist_c
        cdef Data**res

        # NOTE: get the farest node in W and nearest node in C
        if is_query:
            max_iterations = self.max_query_iterations
        else:
            max_iterations = self.max_insert_iterations
        max_dist_w = 0
        min_dist_c = self.bytes_per_vector + 1
        for i in range(self.num_entry):
            eq_dist = self.vec_distance(self.entry_node[i].vector, cur_vec)
            self.C[i].dist = eq_dist
            self.C[i].data = self.entry_node[i]
            if i < self.ef * 10:
                self.W[i].dist = eq_dist
                self.W[i].data = self.entry_node[i]

            self.V[i] = self.entry_node[i]
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
            # if c_near.dist > w_far.dist:
                self.num_count += 1
                break

            if v_len < search_v_max:
                self.V[v_len] = c_near.data
                v_len += 1

            for i in range(c_near.data.num_out):
                candi_node = c_near.data._neighbor[i]
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

                    eq_dist = self.vec_distance(candi_node.vector, cur_vec)
                    count += 1
                    if w_len < self.ef * 10:
                        self.W[w_len].data = candi_node
                        self.W[w_len].dist = eq_dist

                        if max_dist_w < eq_dist:
                            max_dist_w = eq_dist
                            w_far = self.W[w_len]

                        w_len += 1
                        # NOTE: insrt this node into C
                        if c_len < search_c_max:
                            self.C[c_len].data = candi_node
                            self.C[c_len].dist = eq_dist
                            c_len += 1

                    elif eq_dist < w_far.dist:
                        # NOTE: insrt this node into W
                        max_dist_w = 0
                        for k in range(w_len):
                            if self.W[k].data == w_far.data:
                                self.W[k].data = candi_node
                                self.W[k].dist = eq_dist
                            if self.W[k].dist > max_dist_w:
                                max_dist_w = self.W[k].dist
                                w_far_new = self.W[k]
                        w_far = w_far_new

                        # NOTE: insrt this node into C
                        if c_len < search_c_max:
                            self.C[c_len].data = candi_node
                            self.C[c_len].dist = eq_dist
                            c_len += 1

            # extract c_near
            for i in range(c_len):
                if self.C[i].data == c_near.data:
                    self.C[i] = self.C[c_len-1]
                    break
            c_len -= 1

        if self.debugging_mode:
            if self.num_data % 1001 == 0:
                print('num of interations {}'.format(count))

        sort_Datadist(self.W, w_len)
        for i in range(self.ef):
            if i < w_len:
                self.res[i] = self.W[i].data
            else:
                self.res[i] = NULL
        res = self.res
        return res

    # NOTE: find the entry point from tree for the NSW
    cdef Data*search_data(self, UCR*vector):
        cdef Node*node
        cdef Data*entry_node
        node = self.root_node
        cdef UST _1
        for _1 in range(self.bytes_per_vector):
            key = vector[_1]
            while node._next == NULL:
                if node.left != NULL:
                    if key < node.key:
                        node = node.left
                    elif key == node.key:
                        if node.child == NULL:
                            node = node.left
                        else:
                            node = node.child
                            break
                    elif key > node.key:
                        if node.right != NULL:
                            node = node.right
                        elif node.child != NULL:
                            node = node.child
                            break
                        else:
                            node = node.left
                elif node.right != NULL:
                    if key < node.key:
                        if node.left != NULL:
                            node = node.left
                        elif node.child != NULL:
                            node = node.child
                            break
                        else:
                            node = node.right
                    elif key == node.key:
                        if node.child != NULL:
                            node = node.child
                            break
                        else:
                            node = node.right
                    elif key > node.key:
                        node = node.right
                else:
                    node = node.child
                    break
        entry_node = node._next
        return entry_node

    cdef void free_trie(self):
        cdef UIDX _
        PyMem_Free(self.V)
        PyMem_Free(self.W)
        PyMem_Free(self.C)
        PyMem_Free(self.res)
        PyMem_Free(self.entry_node)
        PyMem_Free(self.cur_vec)
        for _ in range(int(self.nodes_capacity/node_size_per_time)):
            PyMem_Free(self.all_nodes[_])
        for _ in range(int(self.data_capacity/data_size_per_time)):
            PyMem_Free(self.all_neigh[_])
        for _ in range(int(self.vec_capacity/data_size_per_time)):
            PyMem_Free(self.all_bytes[_])
        for _ in range(int(self.data_capacity/data_size_per_time)):
            PyMem_Free(self.all_data[_])
        PyMem_Free(self.all_neigh)
        PyMem_Free(self.all_nodes)
        PyMem_Free(self.all_bytes)
        PyMem_Free(self.all_data)

    cdef vec_distance(self, UCR*va, UCR*vb):
        cdef UST i, dist
        dist = 0
        for i in range(self.bytes_per_vector):
            if va[i] != vb[i]:
                dist += 1
        return dist

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

    def __dealloc__(self):
        self.free_trie()

    def debugging(self):
        print('iteration stoped by break {}'.format(self.num_count))
        cdef int i
        cdef int j

        for i in range(self.num_data):
            if (i < 10) or (i+10 > self.num_data):
                res = []
                dist = []
                for j in range(self.all_data[0][i].num_out):
                    res.append(self.all_data[0][i]._neighbor[j].doc_id)
                    dist.append(self.vec_distance(self.all_data[0][i].vector,
                                self.all_data[0][i]._neighbor[j].vector))
                print(res)
                print(dist)
                print('-'*100)

    cpdef destroy(self):
        self.free_trie()

    cpdef _re_search(self, n):
        cdef Data*cur_node
        cdef UIDX i
        for _ in range(n):
            for i in range(self.num_data):
                n_block = int(i / data_size_per_time)
                n_position = i - n_block * data_size_per_time
                cur_node = &self.all_data[n_block][n_position]
                self.assign_neighbors(cur_node)
