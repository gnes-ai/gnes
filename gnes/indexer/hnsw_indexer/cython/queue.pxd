# cython: language_level=3

ctypedef void* queue_value

cdef struct queue_entry:
    queue_value data
    queue_entry *prev
    queue_entry *next

cdef struct queue:
    queue_entry *head
    queue_entry *tail


cdef queue* init_queue()

cdef void queue_free(queue* q_ptr)

cdef void queue_push_head(queue* q_ptr, queue_value data)

cdef queue_value queue_pop_head(queue* q_ptr)

cdef queue_value queue_peak_head(queue* q_ptr)

cdef void queue_push_tail(queue* q_ptr, queue_value data)

cdef queue_value queue_pop_tail(queue* q_ptr)

cdef queue_value queue_peak_tail(queue* q_ptr)

cdef bint queue_is_empty(queue* q_ptr)
