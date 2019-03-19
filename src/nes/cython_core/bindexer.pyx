# cython: language_level=3, wraparound=False, boundscheck=False

# noinspection PyUnresolvedReferences
from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from cpython cimport array

ctypedef unsigned int UIDX
DEF alloc_size_per_time = 200


cdef struct Node:
    Node*left
    Node*right
    Node*child
    unsigned char key
    UIDX*value

cdef struct Counter:
    UIDX num_unique_keys
    UIDX num_total_keys

cdef Node*create_node():
    node = <Node*> PyMem_Malloc(sizeof(Node))
    node.left = NULL
    node.right = NULL
    node.child = NULL
    node.value = NULL
    node.key = 0
    return node

cdef UIDX bytes_to_label(unsigned char *all_ids, unsigned short bytes_per_label):
    cdef UIDX label
    label = 0
    for _ in range(bytes_per_label):
        label += (256**_) * all_ids[_]
    return label

cdef void free_post_order(Node*node):
    if node:
        free_post_order(node.child)
        free_post_order(node.left)
        free_post_order(node.right)
        PyMem_Free(node.value)
        node.value = NULL
        PyMem_Free(node.right)
        node.right = NULL
        PyMem_Free(node.left)
        node.left = NULL
        PyMem_Free(node.child)
        node.child = NULL

cdef unsigned long get_memory_size(Node*node):
    cdef unsigned long cur_size
    cur_size = 0
    if node:
        if node.value:
            cur_size += sizeof(UIDX) * (node.value[1] + 2)
        cur_size += sizeof(node[0])
        cur_size += get_memory_size(node.child)
        cur_size += get_memory_size(node.left)
        cur_size += get_memory_size(node.right)
    return cur_size

cdef class IndexCore:
    cdef Node*root_node
    cdef Counter cnt
    cdef unsigned short bytes_per_vector
    cdef unsigned short bytes_per_label
    cdef unsigned char*_chunk_data

    cdef void _index_value(self, Node*node, UIDX _id):
        if node.value and node.value[0] == node.value[1]:
            new_value = <UIDX*> PyMem_Realloc(node.value,
                                              (node.value[1] + alloc_size_per_time + 2) * sizeof(UIDX))
            if not new_value:
                raise MemoryError()
            node.value = new_value
            node.value[1] += alloc_size_per_time
        elif not node.value:
            node.value = <UIDX*> PyMem_Malloc(alloc_size_per_time * sizeof(UIDX))
            if not node.value:
                raise MemoryError()
            node.value[0] = 0
            node.value[1] = alloc_size_per_time - 2  # first two are reserved for counting
            self.cnt.num_unique_keys += 1
        #(node.value + node.value[0] + 2)[0] = self.cnt.num_total_keys
        (node.value + node.value[0] + 2)[0] = _id
        node.value[0] += 1
        self.cnt.num_total_keys += 1

    cpdef void index_chunk(self, unsigned char *data, const UIDX num_total, unsigned char *all_ids):
        self._chunk_data = data
        self.cnt.num_total_keys = num_total
        self._all_ids = all_ids

    cpdef find_chunk(self, unsigned char *query):
        cdef array.array final_result = array.array('L')
        cdef unsigned char *pt
        cdef UIDX _0
        cdef unsigned short _1
        cdef unsigned char is_match
        pt = self._chunk_data
        pl = self._all_ids
        for _0 in range(self.cnt.num_total_keys):
            is_match = 1
            for _1 in range(self.bytes_per_vector):
                if (query + _1)[0] != (pt + _1)[0]:
                    is_match = 0
                    break
            if is_match == 1:
                final_result.append(bytes_to_label(pl, self.bytes_per_label))
            pt += self.bytes_per_vector
            pl += self.bytes_per_label
        return final_result

    cpdef find_batch_chunk(self, unsigned char *query, const UIDX num_query):
        cdef array.array final_result = array.array('L')
        cdef array.array final_idx = array.array('L')
        cdef unsigned char *pt
        cdef unsigned char *q_pt
        cdef UIDX _0
        cdef UIDX _1
        cdef unsigned short _2
        cdef unsigned char is_match
        pt = self._chunk_data
        for _0 in range(self.cnt.num_total_keys):
            q_pt = query
            for _1 in range(num_query):
                pl = self._all_ids
                is_match = 1
                for _2 in range(self.bytes_per_vector):
                    if (q_pt + _2)[0] != (pt + _2)[0]:
                        is_match = 0
                        break
                if is_match == 1:
                    final_result.append(bytes_to_label(pl, self.bytes_per_label))
                    final_idx.append(_1)
                q_pt += self.bytes_per_vector
                pl += self.bytes_per_label
            pt += self.bytes_per_vector
        return final_idx, final_result

    cpdef contains_chunk(self, unsigned char *query, const UIDX num_query):
        cdef array.array final_result = array.array('B', [0] * num_query)
        cdef unsigned char *pt
        cdef unsigned char *q_pt
        cdef UIDX _0
        cdef UIDX _1
        cdef unsigned short _2
        cdef unsigned char is_match
        pt = self._chunk_data
        for _0 in range(self.cnt.num_total_keys):
            q_pt = query
            for _1 in range(num_query):
                is_match = 1
                for _2 in range(self.bytes_per_vector):
                    if (q_pt + _2)[0] != (pt + _2)[0]:
                        is_match = 0
                        break
                if is_match == 1:
                    final_result[_1] = 1
                q_pt += self.bytes_per_vector
            pt += self.bytes_per_vector
        return final_result

    cpdef find_batch_trie(self, unsigned char *query, const UIDX num_query):
        cdef array.array final_result = array.array('L')
        cdef array.array final_idx = array.array('L')
        cdef Node*node
        cdef unsigned char *q_pt
        cdef UIDX _0
        cdef unsigned short _1
        cdef unsigned char is_match
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
            if is_match == 1 and node.value:
                for _2 in range(2, node.value[0] + 2):
                    final_result.append(node.value[_2])
                    final_idx.append(_0)
            q_pt += self.bytes_per_vector
        return final_idx, final_result

    cpdef find_trie(self, unsigned char *query):
        cdef array.array final_result = array.array('L')
        cdef Node*node
        cdef unsigned short _1
        cdef UIDX _2
        cdef unsigned char is_match
        node = self.root_node
        is_match = 1
        for _1 in range(self.bytes_per_vector):
            key = query[_1]
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
        if is_match == 1 and node.value:
            for _2 in range(2, node.value[0] + 2):
                final_result.append(node.value[_2])
        return final_result

    cpdef contains_trie(self, unsigned char *query, const UIDX num_query):
        cdef array.array final_result = array.array('B', [0] * num_query)
        cdef Node*node
        cdef unsigned char *q_pt
        cdef UIDX _0
        cdef unsigned short _1
        cdef unsigned char is_match
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
            if is_match == 1 and node.value:
                final_result[_0] = 1
            q_pt += self.bytes_per_vector
        return final_result

    cpdef void index_trie(self, unsigned char *data, const UIDX num_total, unsigned char *all_ids):
        cdef Node*node
        cdef UIDX _0
        cdef unsigned short _1
        cdef UIDX _id

        if not self.root_node:
            self.root_node = create_node()

        for _0 in range(num_total):
            node = self.root_node
            for _1 in range(self.bytes_per_vector):
                key = data[_1]
                while node:
                    if node.key == 0 or node.key == key:
                        node.key = key
                        if not node.child:
                            node.child = create_node()
                        node = node.child
                        break
                    elif key < node.key:
                        if not node.left:
                            node.left = create_node()
                        node = node.left
                    elif key > node.key:
                        if not node.right:
                            node.right = create_node()
                        node = node.right
            _id = bytes_to_label(all_ids, self.bytes_per_label)
            self._index_value(node, _id)
            data += self.bytes_per_vector
            # 4 bytes for a unsigned int
            all_ids += self.bytes_per_label

    cdef void free_trie(self):
        free_post_order(self.root_node)
        PyMem_Free(self.root_node)
        self.root_node = NULL
        self.cnt.num_total_keys = 0
        self.cnt.num_unique_keys = 0

    @property
    def counter(self):
        return {
            'num_keys': self.cnt.num_total_keys,
            'num_unique_keys': self.cnt.num_unique_keys
        }

    @property
    def size(self):
        return self.cnt.num_total_keys

    @property
    def memory_size(self):
        return get_memory_size(self.root_node)

    def __cinit__(self, bytes_per_vector, bytes_per_label):
        self.bytes_per_vector = bytes_per_vector
        self.bytes_per_label = bytes_per_label

    def __dealloc__(self):
        self.free_trie()

    cpdef destroy(self):
        self.free_trie()
