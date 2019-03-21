# cython: language_level=3


ctypedef void* value_t

cdef struct pq_entity:
    value_t value
    float priority

cdef struct pq_node:
    pq_node* parent
    pq_node* left
    pq_node* right
    pq_node* child
    pq_entity* entity


cdef struct heappq:
    pq_node* root
    pq_node* min_node
    pq_node* max_node
    size_t size


cdef heappq* init_heappq()

cdef void free_heappq(heappq* pq)

cdef void heappq_push(heappq* pq, float priority, value_t value)

cdef pq_entity* heappq_pop_min(heappq* pq)

cdef pq_entity* heappq_pop_max(heappq* pq)

cdef pq_entity* heappq_peak_min(heappq* pq)

cdef pq_entity* heappq_peak_max(heappq* pq)
