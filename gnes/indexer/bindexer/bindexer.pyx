# cython: language_level=3, wraparound=False, boundscheck=False

# noinspection PyUnresolvedReferences

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from cpython cimport array
import time

ctypedef unsigned int UIDX

DEF data_size_per_time = 10000
DEF node_size_per_time = 100000
DEF data_blocks_increment = 100
DEF node_blocks_increment = 100

cdef struct Node:
    Node*left
    Node*right
    Node*child
    unsigned char key
    Data*_next

cdef struct Data:
    UIDX doc_id
    Data*_next


cdef UIDX bytes_to_label(unsigned char *all_ids, unsigned short bytes_per_label):
    cdef UIDX label
    cdef unsigned short _
    label = 0
    for _ in range(bytes_per_label):
        label += (256**_) * all_ids[_]
    return label

cdef class IndexCore:
    cdef Node*root_node
    cdef unsigned short bytes_per_vector
    cdef unsigned short bytes_per_label

    cdef Data**all_data
    cdef Node**all_nodes

    cdef UIDX nodes_capacity
    cdef UIDX data_capacity

    cdef UIDX max_data_blocks
    cdef UIDX max_node_blocks

    cdef UIDX num_nodes
    cdef UIDX num_data

    cdef void _index_value(self, Node*node, UIDX _id):
        #Data*dnode

        cdef Data* r
        cdef UIDX n_block
        cdef UIDX n_position

        if self.num_data >= self.data_capacity:
            self.data_capacity += data_size_per_time
            r = <Data*> PyMem_Malloc(sizeof(Data)*data_size_per_time)
            n_block = int(self.data_capacity / data_size_per_time)
            # if all data list should be updated
            if n_block > self.max_data_blocks:
                self.all_data = <Data**> PyMem_Realloc(
                    self.all_data,
                    sizeof(Data*)*(self.max_data_blocks+data_blocks_increment))
                self.max_data_blocks += data_blocks_increment
            # then apppend to the existing list
            self.all_data[n_block - 1] = r

        n_block = int(self.data_capacity / data_size_per_time) - 1
        n_position = self.num_data + data_size_per_time - self.data_capacity
        if node._next == NULL:
            node._next = &self.all_data[n_block][n_position]
            node._next.doc_id = _id
            node._next._next = NULL
        else:
            new_node = node._next
            while new_node._next != NULL:
                new_node = new_node._next
            new_node._next = &self.all_data[n_block][n_position]
            new_node._next.doc_id = _id
            new_node._next._next = NULL

        '''
        new_node = node._next
        if new_node == NULL:
            print('new_node is null')
        while new_node != NULL:
            new_node = new_node._next
        new_node = &self.all_data[n_block][n_position]
        new_node.doc_id = _id
        new_node._next = NULL
        '''
        self.num_data += 1

    cpdef find_batch_trie(self, unsigned char *query, const UIDX num_query):
        cdef array.array final_result = array.array('L')
        cdef array.array final_idx = array.array('L')
        cdef Node*node
        cdef Data*dnode
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

    cpdef void index_trie(self, unsigned char *data, const UIDX num_total, unsigned char *all_ids):
        cdef Node*node
        cdef UIDX _0
        cdef unsigned short _1
        cdef UIDX _id

        if not self.root_node:
            self.all_nodes = <Node**> PyMem_Malloc(sizeof(Node*)*node_blocks_increment)
            self.all_data = <Data**> PyMem_Malloc(sizeof(Data*)*data_blocks_increment)
            block_nodes = <Node*> PyMem_Malloc(sizeof(Node)*node_size_per_time)
            block_data = <Data*> PyMem_Malloc(sizeof(Data)*data_size_per_time)
            self.max_node_blocks = node_blocks_increment
            self.max_data_blocks = data_blocks_increment
            self.all_nodes[0] = block_nodes
            self.all_data[0] = block_data

            self.nodes_capacity = node_size_per_time
            self.data_capacity = data_size_per_time
            self.num_nodes = 0
            self.num_data = 0
            self.root_node = self.new_node()

        for _0 in range(num_total):
            node = self.root_node
            for _1 in range(self.bytes_per_vector):
                key = data[_1]
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
            self._index_value(node, _id)
            data += self.bytes_per_vector
            # 4 bytes for a unsigned int
            all_ids += self.bytes_per_label

    cdef Node* new_node(self):
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

    cdef void free_trie(self):
        cdef UIDX _
        for _ in range(int(self.data_capacity/data_size_per_time)):
            PyMem_Free(self.all_data[_])
        for _ in range(int(self.nodes_capacity/node_size_per_time)):
            PyMem_Free(self.all_nodes[_])
        PyMem_Free(self.all_nodes)
        PyMem_Free(self.all_data)
        self.data_capacity = 0
        self.nodes_capacity = 0

    def __cinit__(self, bytes_per_vector, bytes_per_label):
        self.bytes_per_vector = bytes_per_vector
        self.bytes_per_label = bytes_per_label

    def __dealloc__(self):
        self.free_trie()

    cpdef destroy(self):
        self.free_trie()
