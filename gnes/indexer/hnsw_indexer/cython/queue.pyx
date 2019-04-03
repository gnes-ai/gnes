# cython: language_level=3

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free


cdef queue* init_queue():
    cdef queue* q = <queue*> PyMem_Malloc(sizeof(queue))
    q.head = NULL
    q.tail = NULL
    q.size = 0
    return q

cdef void queue_free(queue* q_ptr):
    while not queue_is_empty(q_ptr):
        queue_pop_head(q_ptr)

    PyMem_Free(q_ptr)


cdef void queue_push_head(queue* q_ptr, queue_value data):
    cdef queue_entry* entry = <queue_entry*> PyMem_Malloc(sizeof(queue_entry))
    entry.data = data
    entry.prev = NULL
    entry.next = q_ptr.head

    if q_ptr.head == NULL:
        q_ptr.head = entry
        q_ptr.tail = entry
    else:
        q_ptr.head.prev = entry
        q_ptr.head = entry
    q_ptr.size += 1


cdef queue_value queue_pop_head(queue* q_ptr):
    cdef queue_entry *entry
    cdef queue_value result

    if queue_is_empty(q_ptr):
        return NULL

    entry = q_ptr.head
    q_ptr.head = entry.next
    result = entry.data

    if q_ptr.head == NULL:
        q_ptr.tail = NULL
    else:
        q_ptr.head.prev = NULL
    q_ptr.size -= 1

    entry.data = NULL
    entry.next = NULL
    PyMem_Free(entry)

    return result


cdef queue_value queue_peak_head(queue *q_ptr):
     if queue_is_empty(q_ptr):
         return NULL
     else:
         return q_ptr.head.data


cdef void queue_push_tail(queue *q_ptr, queue_value data):
    cdef queue_entry* entry = <queue_entry*> PyMem_Malloc(sizeof(queue_entry))
    entry.data = data
    entry.prev = q_ptr.tail
    entry.next = NULL

    if q_ptr.tail == NULL:
        q_ptr.head = entry
        q_ptr.tail = entry
    else:
        q_ptr.tail.next = entry
        q_ptr.tail = entry
    q_ptr.size += 1

cdef queue_value queue_pop_tail(queue* q_ptr):
    cdef queue_entry *entry
    cdef queue_value result

    if queue_is_empty(q_ptr):
        return NULL

    entry = q_ptr.tail
    q_ptr.tail = entry.prev
    result = entry.data

    if q_ptr.tail == NULL:
        q_ptr.head = NULL
    else:
        q_ptr.tail.next = NULL
    q_ptr.size -= 1

    entry.data = NULL
    entry.prev = NULL
    PyMem_Free(entry)
    return result

cdef queue_value queue_peak_tail(queue* q_ptr):
    if queue_is_empty(q_ptr):
        return NULL
    else:
        return q_ptr.tail.data

cdef bint queue_is_empty(queue* q_ptr):
    return q_ptr.head == NULL