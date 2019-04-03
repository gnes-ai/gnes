# cython: language_level=3, wraparound=False, boundscheck=False

# noinspection PyUnresolvedReferences
import os
import struct

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from cpython cimport array
from cpython.bytes cimport PyBytes_FromStringAndSize


from libc.stdlib cimport rand, RAND_MAX
from libc.string cimport memcpy
from libc.math cimport log, floor, abs

from hnsw_cpy.cython_core.heappq cimport heappq, pq_entity, init_heappq, free_heappq, heappq_push, heappq_pop_min, heappq_peak_min, heappq_pop_max, heappq_peak_max
from hnsw_cpy.cython_core.queue cimport queue, init_queue, queue_push_tail, queue_pop_head, queue_free, queue_is_empty
from hnsw_cpy.cython_core.prehash cimport prehash_map, init_prehash_map, prehash_insert, prehash_get, prehash_free


cdef hnswNode* create_node(UIDX id, USHORT level, BVECTOR vector, USHORT bytes_num):
     cdef hnswNode *node = <hnswNode*> PyMem_Malloc(sizeof(hnswNode))
     node.id = id
     node.level = level
     node.low_level = 0
     node.next = NULL
     cdef USHORT N = bytes_num * sizeof(UCHAR)

     node.vector = <BVECTOR> PyMem_Malloc(N)
     memcpy(node.vector, vector, N)

     node.edges = <hnsw_edge_set**> PyMem_Malloc((level+1) * sizeof(hnsw_edge_set*))

     cdef hnsw_edge_set* edge_set
     cdef USHORT l
     for l in range(level+1):
         edge_set = <hnsw_edge_set*> PyMem_Malloc(sizeof(hnsw_edge_set))
         edge_set.size = 0
         edge_set.indegree = 0
         edge_set.head_ptr = NULL
         edge_set.last_ptr = NULL

         node.edges[l] = edge_set

     return node

cdef void _add_edge(hnswNode* from_node, hnswNode* target_node, DIST dist, UINT level):
    cdef hnsw_edge* edge = <hnsw_edge*> PyMem_Malloc(sizeof(hnsw_edge))
    edge.node = target_node
    edge.dist = dist
    edge.next = NULL

    cdef hnsw_edge_set* edge_set = from_node.edges[level]
    if edge_set.head_ptr == NULL:
        edge_set.head_ptr = edge
        edge_set.last_ptr = edge
    else:
        edge_set.last_ptr.next = edge
        edge_set.last_ptr = edge

    edge_set.size += 1

    target_node.edges[level].indegree += 1


cdef queue* _empty_edge_set(hnswNode* node, USHORT level, bint check_island):
    cdef queue* island_nodes = init_queue()
    cdef hnsw_edge_set* edge_set = node.edges[level]
    cdef hnsw_edge* head_edge = edge_set.head_ptr

    while head_edge != NULL:
        if check_island:
            queue_push_tail(island_nodes, head_edge.node)
            # WIP: must under the condition: check_island = True
            # WIP: DONT MODIFY THIS CODE LINE
            head_edge.node.edges[level].indegree -= 1

        edge_set.head_ptr = head_edge.next
        head_edge.next = NULL
        PyMem_Free(head_edge)
        head_edge = edge_set.head_ptr

    edge_set.size = 0
    edge_set.head_ptr = NULL
    edge_set.last_ptr = NULL
    return island_nodes

cpdef USHORT hamming_dist(BVECTOR x, BVECTOR y, USHORT datalen):
    cdef USHORT i, dist = 0
    cdef UCHAR byte_x, byte_y, byte_z

    for i in range(datalen):
        byte_x = x[i]
        byte_y = y[i]
        byte_z = byte_x ^ byte_y

        if byte_z > 0:
            dist += 1
    return dist


cdef void _free_node(hnswNode* node):
    cdef USHORT level = node.level
    cdef USHORT low_level = node.low_level
    cdef USHORT l
    cdef queue* neighbors

    for l in range(low_level, level+1):
        neighbors = _empty_edge_set(node, l, False)
        queue_free(neighbors)

        PyMem_Free(node.edges[l])
        node.edges[l] = NULL

    PyMem_Free(node.edges)
    node.edges = NULL
    PyMem_Free(node.vector)
    node.vector = NULL
    node.next = NULL
    PyMem_Free(node)

cdef class IndexHnsw:
    cdef hnswConfig* config
    cdef UINT total_size
    cdef USHORT bytes_num
    cdef USHORT max_level
    cdef hnswNode* entry_ptr


    cpdef void index(self, UIDX id, BVECTOR vector):
        self._add_node(id, vector)

    cdef void _add_node(self, UIDX id, BVECTOR vector):
        """Add node to the hnsw graph"""

        cdef hnswNode* new_node
        cdef hnswNode* entry_ptr = self.entry_ptr
        self.total_size += 1

        # create the root node at level 0
        if entry_ptr == NULL:
            new_node = create_node(id, 0, vector, self.bytes_num)
            self.entry_ptr = new_node

            return

        # the HNSW is not empty, we have an entry point

        # level at which the node will be added
        cdef USHORT level = self._random_level()
        new_node = create_node(id, level, vector, self.bytes_num)

        cdef DIST min_dist = hamming_dist(vector, self.entry_ptr.vector, self.bytes_num)

        cdef int l = self.max_level

        cdef hnsw_edge* result_item
        while l > level:
            # search for the closest neighbor
            result_item = self.greedy_closest_neighbor(vector, entry_ptr, min_dist, l)
            entry_ptr = result_item.node
            min_dist = result_item.dist

            PyMem_Free(result_item)

            l -= 1


        l = min(self.max_level, level)
        cdef hnswNode* neighbor
        cdef UINT m_max
        cdef DIST dist
        cdef heappq* neighbors_pq
        cdef heappq* selected_pq
        cdef pq_entity* pq_e
        cdef USHORT _l

        while l >= 0:
            # navigate the graph and create edges with the closest nodes we find
            neighbors_pq = self.search_level(vector, entry_ptr, self.config.ef_construction, l)
            selected_pq = self._select_neighbors(vector, neighbors_pq, self.config.m, l, True)
            free_heappq(neighbors_pq)

            pq_e = heappq_peak_min(selected_pq)
            if pq_e.priority <= self.config.epsilon:
                neighbor = <hnswNode*> pq_e.value
                new_node.next = neighbor.next
                neighbor.next = new_node
                new_node.low_level = l+1

                for _l in range(new_node.low_level):
                    PyMem_Free(new_node.edges[_l])
                    new_node.edges[_l] = NULL
                    new_node.edges[_l] = neighbor.edges[_l]

                free_heappq(selected_pq)
                break

            while selected_pq.size > 0:
                pq_e = heappq_pop_max(selected_pq)
                dist = pq_e.priority
                neighbor = <hnswNode*> pq_e.value
                pq_e.value = NULL
                PyMem_Free(pq_e)

                entry_ptr = neighbor

                _add_edge(new_node, neighbor, dist, l)
                _add_edge(neighbor, new_node, dist, l)

                m_max = self.config.m_max
                if l == 0:
                    m_max = self.config.m_max_0
                if neighbor.edges[l].size > m_max:
                    self._prune_neighbors(neighbor, self.config.m, l)


            l -= 1
            free_heappq(selected_pq)

        if level > self.max_level:
            self.max_level = level
            self.entry_ptr = new_node


    cdef heappq* search_level(self, BVECTOR query, hnswNode *entry_ptr, UINT ef, USHORT level):
        cdef DIST dist = hamming_dist(query, entry_ptr.vector, self.bytes_num)

        cdef heappq* candidates_pq = init_heappq()
        cdef heappq* result_pq = init_heappq()
        heappq_push(candidates_pq, dist, entry_ptr)
        heappq_push(result_pq, dist, entry_ptr)

        cdef set visited_nodes = set()
        visited_nodes.add(entry_ptr.id)

        cdef hnswNode* candidate
        cdef hnswNode* neighbor

        cdef DIST lower_bound

        cdef hnsw_edge* next_edge
        cdef hnsw_edge_set* edge_set

        cdef pq_entity* pq_e
        cdef pq_entity* _e

        cdef USHORT not_found_steps = 0

        while candidates_pq.size > 0:
            pq_e = heappq_pop_min(candidates_pq)
            priority = pq_e.priority
            candidate = <hnswNode*> pq_e.value
            pq_e.value = NULL
            PyMem_Free(pq_e)

            lower_bound = heappq_peak_max(result_pq).priority

            # if priority > lower_bound and result_pq.size >= ef:
            if priority > lower_bound or not_found_steps >= ef:
                break
            elif priority == lower_bound:
                not_found_steps += 1

            edge_set = candidate.edges[level]
            next_edge = edge_set.head_ptr

            while next_edge != NULL:
                neighbor = next_edge.node

                if neighbor.id in visited_nodes:
                    next_edge = next_edge.next
                    continue

                visited_nodes.add(neighbor.id)

                dist = hamming_dist(query, neighbor.vector, self.bytes_num)

                if dist < lower_bound or result_pq.size < ef:
                    heappq_push(candidates_pq, dist, neighbor)
                    heappq_push(result_pq, dist, neighbor)

                    if lower_bound < dist:
                        lower_bound = dist

                    if result_pq.size > ef:
                        _e = heappq_pop_max(result_pq)
                        _e.value = NULL
                        PyMem_Free(_e)

                        lower_bound = heappq_peak_max(result_pq).priority

                    not_found_steps = 0

                # TODO: uncomment the following codes to enlarge search space
                # elif dist == lower_bound:
                #     heappq_push(candidates_pq, dist, neighbor)

                next_edge = next_edge.next

        visited_nodes.clear()

        free_heappq(candidates_pq)
        candidates_pq = NULL

        return result_pq

    cdef hnsw_edge* greedy_closest_neighbor(self, BVECTOR query, hnswNode *entry_ptr, DIST min_dist, USHORT level):
        cdef DIST _min_dist = min_dist
        cdef DIST dist

        cdef hnswNode *node_ptr

        cdef hnswNode *closest_neighbor = entry_ptr

        cdef hnsw_edge_set* edge_set
        cdef hnsw_edge* next_edge
        cdef set visited_nodes = set()

        cdef queue* candidates = init_queue()
        queue_push_tail(candidates, entry_ptr)
        visited_nodes.add(entry_ptr.id)

        while not queue_is_empty(candidates):
            node_ptr = <hnswNode*> queue_pop_head(candidates)

            edge_set = node_ptr.edges[level]
            next_edge = edge_set.head_ptr

            while next_edge != NULL:
                node_ptr = next_edge.node

                if node_ptr.id in visited_nodes:
                    next_edge = next_edge.next
                    continue
                visited_nodes.add(node_ptr.id)

                dist = hamming_dist(query, node_ptr.vector, self.bytes_num)
                if dist < _min_dist:
                    _min_dist = dist
                    closest_neighbor = node_ptr
                    while not queue_is_empty(candidates):
                        queue_pop_head(candidates)
                    queue_push_tail(candidates, node_ptr)

                elif dist == _min_dist:
                    queue_push_tail(candidates, node_ptr)


                next_edge = next_edge.next

        visited_nodes.clear()
        queue_free(candidates)

        cdef hnsw_edge* edge = <hnsw_edge*> PyMem_Malloc(sizeof(hnsw_edge))
        edge.node = closest_neighbor
        edge.dist = _min_dist
        return edge


    cdef heappq* _select_neighbors(self, BVECTOR query, heappq* neighbors_pq, USHORT ensure_k, USHORT level, bint extend_candidates):
        cdef heappq* result_pq = init_heappq()
        cdef set visited_nodes = set()

        cdef hnsw_edge* next_edeg
        cdef hnsw_edge_set* edge_set
        cdef DIST dist
        cdef pq_entity* pq_e

        if extend_candidates or neighbors_pq.size < ensure_k:
            while neighbors_pq.size > 0:
                pq_e = heappq_pop_min(neighbors_pq)
                priority = pq_e.priority
                candidate = <hnswNode*> pq_e.value
                pq_e.value = NULL
                PyMem_Free(pq_e)

                if candidate.id in visited_nodes:
                    continue

                heappq_push(result_pq, priority, candidate)
                visited_nodes.add(candidate.id)

                edge_set = candidate.edges[level]
                next_edge = edge_set.head_ptr
                while next_edge != NULL:
                    candidate = next_edge.node

                    if candidate.id in visited_nodes:
                        next_edge = next_edge.next
                        continue

                    visited_nodes.add(candidate.id)

                    dist = hamming_dist(query, candidate.vector, self.bytes_num)

                    heappq_push(result_pq, dist, candidate)
                    next_edge = next_edge.next

        else:
            while neighbors_pq.size > 0 and result_pq.size < ensure_k:
                pq_e = heappq_pop_min(neighbors_pq)
                priority = pq_e.priority
                candidate = <hnswNode*> pq_e.value
                pq_e.value = NULL
                PyMem_Free(pq_e)

                heappq_push(result_pq, priority, candidate)



        while result_pq.size > ensure_k:
            pq_e = heappq_pop_max(result_pq)
            pq_e.value = NULL
            PyMem_Free(pq_e)

        visited_nodes.clear()

        return result_pq

    cdef void _prune_neighbors(self, hnswNode* node, UINT k, USHORT level):
        cdef heappq* neighbors_pq = init_heappq()
        cdef heappq* selected_pq

        cdef hnsw_edge_set* edge_set = node.edges[level]
        cdef hnsw_edge* next_edge = edge_set.head_ptr

        cdef DIST dist
        cdef hnswNode* neighbor
        while next_edge != NULL:
            neighbor = next_edge.node
            dist = next_edge.dist

            heappq_push(neighbors_pq, dist, neighbor)

            next_edge = next_edge.next

        selected_pq = self._select_neighbors(node.vector, neighbors_pq, k, level, True)
        free_heappq(neighbors_pq)

        cdef queue* island_nodes = _empty_edge_set(node, level, True)
        cdef pq_entity* pq_e
        while selected_pq.size > 0:
            pq_e = heappq_pop_min(selected_pq)
            dist = pq_e.priority
            neighbor = <hnswNode*> pq_e.value
            pq_e.value = NULL
            PyMem_Free(pq_e)
            _add_edge(node, neighbor, dist, level)

        free_heappq(selected_pq)
        neighbors_pq = NULL
        selected_pq = NULL

        cdef hnswNode* island
        cdef hnswNode* island_neighbor
        cdef hnsw_edge* result_item
        cdef hnswNode* entry_ptr
        cdef heappq* island_neighbors
        cdef heappq* island_selected
        cdef DIST min_dist
        cdef USHORT l

        while not queue_is_empty(island_nodes):
            island = <hnswNode*> queue_pop_head(island_nodes)
            if island.edges[level].indegree > int(0.5*self.config.m):
                continue

            entry_ptr = self.entry_ptr
            l = self.max_level

            min_dist = hamming_dist(island.vector, entry_ptr.vector, self.bytes_num)

            # add new incoming edges
            while l > level:
                result_item = self.greedy_closest_neighbor(island.vector, entry_ptr, min_dist, l)
                min_dist = result_item.dist
                entry_ptr = result_item.node
                PyMem_Free(result_item)

                l -= 1

            island_neighbors = self.search_level(island.vector, entry_ptr, self.config.ef_construction, level)
            island_selected = self._select_neighbors(island.vector, island_neighbors, self.config.m, level, True)
            free_heappq(island_neighbors)

            while island_selected.size > 0:
                pq_e = heappq_pop_max(island_selected)
                dist = pq_e.priority
                island_neighbor = <hnswNode*> pq_e.value
                pq_e.value = NULL
                PyMem_Free(pq_e)
                _add_edge(island_neighbor, island, dist, level)
            free_heappq(island_selected)

        queue_free(island_nodes)

    cdef USHORT _random_level(self):
        cdef double r = rand() / RAND_MAX
        cdef double f = floor(-log(r) * self.config.level_multiplier)

        return int(f)

    cpdef list query(self, BVECTOR query, USHORT top_k):
        cdef hnswNode* entry_ptr = self.entry_ptr

        cdef DIST min_dist = hamming_dist(query, entry_ptr.vector, self.bytes_num)
        cdef int l = self.max_level
        cdef hnsw_edge* result_item
        while l > 0:
            result_item = self.greedy_closest_neighbor(query, entry_ptr, min_dist, l)
            entry_ptr = result_item.node
            min_dist = result_item.dist
            PyMem_Free(result_item)

            l -= 1


        cdef UINT ef = max(2*self.config.ef, top_k)
        cdef heappq* neighbors_pq = self.search_level(query, entry_ptr, ef, 0)
        cdef USHORT count = 0

        cdef list result = []

        cdef pq_entity* pq_e
        cdef hnswNode* next_node
        cdef DIST dist
        while neighbors_pq.size > 0:
            pq_e = heappq_pop_min(neighbors_pq)
            dist = pq_e.priority
            next_node = <hnswNode*> pq_e.value
            pq_e.value = NULL
            PyMem_Free(pq_e)
            while next_node != NULL:
                if count >= top_k:
                    break
                result.append({
                    'id': next_node.id,
                    'distance': dist
                })
                count += 1
                next_node = next_node.next

            if count >= top_k:
                break

        free_heappq(neighbors_pq)
        neighbors_pq = NULL
        return result

    cpdef batch_query(self, BVECTOR query, const USHORT num_query, const USHORT k):
        cdef UIDX _0
        cdef USHORT _1
        cdef BVECTOR q_key = <unsigned char*> PyMem_Malloc(sizeof(unsigned char) * self.bytes_num)
        result = []
        for _0 in range(num_query):
            for _1 in range(self.bytes_num):
                q_key[_1] = query[_1]
            q_result = self.query(q_key, k)
            result.append(q_result)

            query += self.bytes_num

        PyMem_Free(q_key)

        return result


    cdef queue* _get_nodes(self):
        cdef set visited_nodes = set()
        cdef queue* nodes_queue = init_queue()
        cdef queue* candidates_queue = init_queue()

        cdef hnswNode* node_ptr = self.entry_ptr
        cdef hnswNode* next_node
        cdef hnswNode* neighbor
        cdef hnsw_edge_set* edge_set
        cdef hnsw_edge* next_edge

        queue_push_tail(candidates_queue, node_ptr)
        visited_nodes.add(node_ptr.id)

        while not queue_is_empty(candidates_queue):
            node_ptr = <hnswNode*> queue_pop_head(candidates_queue)

            # get linked nodes
            next_node = node_ptr.next
            while next_node != NULL:
                if next_node.id in visited_nodes:
                    next_node = next_node.next
                    continue
                queue_push_tail(candidates_queue, next_node)
                visited_nodes.add(next_node.id)
                next_node = next_node.next

            edge_set = node_ptr.edges[0]
            next_edge = edge_set.head_ptr

            while next_edge != NULL:
                neighbor = next_edge.node
                #if neighbor == NULL:
                #    next_edge = next_edge.next
                #    continue

                if neighbor.id in visited_nodes:
                    next_edge = next_edge.next
                    continue

                queue_push_tail(candidates_queue, neighbor)
                visited_nodes.add(neighbor.id)

                next_edge = next_edge.next

            queue_push_tail(nodes_queue, node_ptr)

        queue_free(candidates_queue)
        visited_nodes.clear()

        return nodes_queue

    cpdef void dump(self, model_path):
        bf_m = open(os.path.join(model_path, 'graph.meta'), 'wb')
        bf_e = open(os.path.join(model_path, 'graph.edges'), 'wb')
        bf_inv = open(os.path.join(model_path, 'graph.inv'), 'wb')

        # dump hnsw config struct
        bd = struct.pack("IHHIiiiiiff", self.total_size, self.bytes_num, self.max_level, self.entry_ptr.id, self.config.ef, self.config.ef_construction, self.config.m, self.config.m_max, self.config.m_max_0, self.config.level_multiplier, self.config.epsilon)
        bf_m.write(bd)

        cdef queue* nodes_queue = self._get_nodes()

        cdef hnsw_edge_set* edge_set
        cdef hnsw_edge* next_edge
        cdef hnswNode* next_node
        cdef hnswNode* prev_node
        cdef int l = 0
        cdef UIDX node_id
        cdef DIST dist

        while not queue_is_empty(nodes_queue):
            node_ptr = <hnswNode*> queue_pop_head(nodes_queue)
            bd = struct.pack("IHH", node_ptr.id, node_ptr.level, node_ptr.low_level)

            bf_m.write(bd + PyBytes_FromStringAndSize(<char*> node_ptr.vector, self.bytes_num))
            bf_e.write(bd)

            next_node = node_ptr.next

            if next_node != NULL:
                prev_node = node_ptr
                _inv_data = b''
                _count = 0
                while next_node != NULL:
                    inv_bd = struct.pack('II', prev_node.id, next_node.id)
                    _inv_data += inv_bd

                    prev_node = next_node
                    next_node = next_node.next
                    _count += 1
                bf_inv.write(struct.pack('H', _count) + _inv_data)

            #l = node_ptr.level

            edges_bytes = b''
            edges_data_size = 0

            for l in range(node_ptr.low_level, node_ptr.level+1):

                edge_set = node_ptr.edges[l]

                level_edges_bytes = struct.pack('HH', l, edge_set.size)

                next_edge = edge_set.head_ptr
                while next_edge != NULL:
                    node_id = next_edge.node.id
                    dist = next_edge.dist
                    bd = struct.pack('If', node_id, dist)
                    level_edges_bytes += bd

                    next_edge = next_edge.next

                level_edge_data_size = 2*sizeof(USHORT) + edge_set.size*(sizeof(UIDX) + sizeof(float))

                edges_bytes += level_edges_bytes
                edges_data_size += level_edge_data_size

                #l -= 1

            edges_bytes = struct.pack('H', edges_data_size) + edges_bytes

            bf_e.write(edges_bytes)

        queue_free(nodes_queue)
        bf_m.close()
        bf_e.close()
        bf_inv.close()

    cpdef void load(self, model_path):

        bf_m = open(os.path.join(model_path, 'graph.meta'), 'rb')

        graph_meta_size = 2*sizeof(UIDX) + 2*sizeof(USHORT) + 5*sizeof(int) + 2*sizeof(float)

        # load hnsw config struct
        binary_data = bf_m.read(graph_meta_size)
        tuple_of_data = struct.unpack("IHHIiiiiiff", binary_data)

        total_size = tuple_of_data[0]
        bytes_num = tuple_of_data[1]
        max_level = tuple_of_data[2]
        entry_id = tuple_of_data[3]

        self.total_size = total_size
        self.bytes_num = bytes_num
        self.max_level = max_level

        self.config.ef = tuple_of_data[4]
        self.config.ef_construction = tuple_of_data[5]
        self.config.m = tuple_of_data[6]
        self.config.m_max = tuple_of_data[7]
        self.config.m_max_0 = tuple_of_data[8]
        self.config.level_multiplier = tuple_of_data[9]
        self.config.epsilon = tuple_of_data[10]

        node_meta_size = sizeof(UIDX) + 2*sizeof(USHORT)
        node_size = node_meta_size + self.bytes_num*sizeof(UCHAR)

        cdef int count = 0
        cdef hnswNode* node_ptr
        cdef prehash_map* nodes_map = init_prehash_map()
        cdef UIDX id
        cdef USHORT level, low_level

        while count < total_size:
            bd = bf_m.read(node_size)
            id, level, low_level = struct.unpack("IHH", bd[:node_meta_size])
            vector = bd[node_meta_size:]
            node_ptr = create_node(id, level, vector, self.bytes_num)
            node_ptr.low_level = low_level
            prehash_insert(nodes_map, id, node_ptr)

            count += 1
        bf_m.close()

        self.entry_ptr = <hnswNode*> prehash_get(nodes_map, entry_id)

        # load graph edges
        bf_e = open(os.path.join(model_path, 'graph.edges'), 'rb')

        count = 0
        cdef hnswNode* neighbor_ptr
        cdef USHORT _level


        while count < total_size:
            bd = bf_e.read(sizeof(UIDX) + 2*sizeof(USHORT))
            id, level, low_level = struct.unpack('IHH', bd)
            node_ptr = <hnswNode*> prehash_get(nodes_map, id)

            bd = bf_e.read(sizeof(USHORT))
            data_len = struct.unpack('H', bd)[0]

            node_edges_data = bf_e.read(data_len)
            _start_pos = 0

            for _level in range(node_ptr.low_level, level+1):
                _l, _size = struct.unpack('HH', node_edges_data[_start_pos:_start_pos+2*sizeof(USHORT)])
                _start_pos += 2*sizeof(USHORT)
                while _size > 0:
                    nid, dist = struct.unpack('If', node_edges_data[_start_pos:_start_pos+sizeof(UIDX) + sizeof(float)])
                    neighbor_ptr = <hnswNode*> prehash_get(nodes_map, nid)
                    _add_edge(node_ptr, neighbor_ptr, dist, _l)
                    _start_pos += sizeof(UIDX) + sizeof(float)
                    _size -= 1

                level -= 1

            count += 1
        bf_e.close()

        # load inverted nodes
        cdef hnswNode* prev_node
        cdef hnswNode* next_node = NULL
        cdef USHORT _0, _1

        bf_inv = open(os.path.join(model_path, 'graph.inv'), 'rb')
        bd = bf_inv.read(sizeof(USHORT))
        while len(bd) > 0:
            _count = struct.unpack('H', bd)[0]
            for _0 in range(_count):
                p_id, n_id = struct.unpack('II', bf_inv.read(2*sizeof(UIDX)))
                if next_node != NULL and next_node.id == p_id:
                    prev_node = next_node
                else:
                    prev_node = <hnswNode*> prehash_get(nodes_map, p_id)

                next_node = <hnswNode*> prehash_get(nodes_map, n_id)

                prev_node.next = next_node
                for _1 in range(next_node.low_level):
                    PyMem_Free(next_node.edges[_1])
                    next_node.edges[_1] = prev_node.edges[_1]

            bd = bf_inv.read(sizeof(USHORT))
        bf_inv.close()

        prehash_free(nodes_map)

    cdef void free_hnsw(self):
        cdef queue* nodes_queue = self._get_nodes()
        while not queue_is_empty(nodes_queue):
            node_ptr = <hnswNode*> queue_pop_head(nodes_queue)
            _free_node(node_ptr)

        queue_free(nodes_queue)
        PyMem_Free(self.config)
        self.config = NULL

        self.entry_ptr = NULL
        self.total_size = 0
        self.max_level = 0


    @property
    def size(self):
        return self.total_size

    @property
    def num_bytes(self):
        return self.bytes_num

    @property
    def memory_size(self):
        raise NotImplemented
        #return get_memory_size(self.root_node)


    def __cinit__(self, bytes_num, **kwargs):
        self.bytes_num = bytes_num

        self.config = <hnswConfig*> PyMem_Malloc(sizeof(hnswConfig))
        self.config.level_multiplier = kwargs.get('level_multiplier', -1)
        self.config.ef = kwargs.get('ef', 20)
        self.config.ef_construction = kwargs.get('ef_construction', 150)
        self.config.m = kwargs.get('m', 12)
        self.config.m_max = kwargs.get('m_max', -1)
        self.config.m_max_0 = kwargs.get('m_max_0', -1)
        self.config.epsilon = kwargs.get('epsilon', 0)

        if self.config.level_multiplier == -1:
            self.config.level_multiplier = 1.0 / log(1.0*self.config.m)

        if self.config.m_max == -1:
            self.config.m_max = int(self.config.m * 1.5)

        if self.config.m_max_0 == -1:
            self.config.m_max_0 = 2 * self.config.m

        print('Ef:\t%d' % self.config.ef)
        print('Ef-construction:\t%d' % self.config.ef_construction)
        print('M:\t%d' % self.config.m)
        print('MMax:\t%d' % self.config.m_max)
        print('MMax0:\t%d' % self.config.m_max_0)
        print('Multiplier:\t%.3f' % self.config.level_multiplier)

        self.entry_ptr = NULL
        self.max_level = 0
        self.total_size = 0

    def __dealloc__(self):
        self.free_hnsw()

    cpdef destroy(self):
        self.free_hnsw()
