# cython: language_level=3

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
cimport cpython

cdef heappq* init_heappq():
    cdef heappq* pq = <heappq*> PyMem_Malloc(sizeof(heappq))
    pq.root = NULL
    pq.min_node = NULL
    pq.max_node = NULL
    pq.size = 0
    return pq

cdef void free_heappq(heappq* pq):
    cdef unsigned int i = 0
    cdef pq_entity* e

    while pq.size > 0:
        if i % 2 == 0:
            e = heappq_pop_max(pq)
        else:
            e = heappq_pop_min(pq)
        e.value = NULL
        PyMem_Free(e)
        i += 1

    PyMem_Free(pq)

cdef void heappq_push(heappq* pq, float priority, value_t value):
    cdef pq_entity* entity = <pq_entity*> PyMem_Malloc(sizeof(pq_entity))

    entity.value = value
    entity.priority = priority

    cdef pq_node* new_node = <pq_node*> PyMem_Malloc(sizeof(pq_node))
    new_node.entity = entity
    new_node.parent = NULL
    new_node.child = NULL
    new_node.left = NULL
    new_node.right = NULL

    pq.size += 1

    cdef pq_node* start_node = pq.root
    if start_node == NULL:
        pq.root = new_node
        pq.min_node = new_node
        pq.max_node = new_node
        return

    cdef bint new_min_node = 1
    cdef bint new_max_node = 1

    while start_node != NULL:
        if priority > start_node.entity.priority:
            new_min_node = 0
            if start_node.right != NULL:
                start_node = start_node.right
            else:
                new_node.parent = start_node
                start_node.right = new_node
                break
        elif priority < start_node.entity.priority:
            new_max_node = 0
            if start_node.left != NULL:
                start_node = start_node.left
            else:
                new_node.parent = start_node
                start_node.left = new_node
                break
        else:
            new_min_node = 0
            new_max_node = 0
            if start_node.child != NULL:
                start_node.child.parent = new_node
                new_node.child = start_node.child

            new_node.parent = start_node
            start_node.child = new_node
            break

    if new_min_node:
        pq.min_node = new_node
    elif new_max_node:
        pq.max_node = new_node


cdef pq_entity* heappq_pop_min(heappq* pq):
    if pq.min_node == NULL:
        return NULL

    pq.size -= 1

    cdef pq_node* result_node = pq.min_node
    cdef pq_node* parent_node = result_node.parent
    cdef pq_node* child_node = result_node.child
    cdef pq_node* right_node = result_node.right

    if child_node != NULL:
        if child_node.child != NULL:
            child_node.child.parent = pq.min_node

        result_node = child_node
        pq.min_node.child = result_node.child

    elif right_node == NULL:
        if parent_node != NULL:
            parent_node.left = NULL
            pq.min_node = parent_node
        else:
            pq.root = NULL
            pq.min_node = NULL
            pq.max_node = NULL

    else:
        if parent_node == NULL:
            right_node.parent = NULL
            pq.root = right_node
        else:
            result_node.right = NULL
            right_node.parent = parent_node
            parent_node.left = right_node

        pq.min_node = right_node
        while pq.min_node.left != NULL:
            pq.min_node = pq.min_node.left
        pq.min_node.left = NULL

    cdef pq_entity* result = result_node.entity
    result_node.entity = NULL
    result_node.left = NULL
    result_node.right = NULL
    result_node.parent = NULL
    result_node.child = NULL
    PyMem_Free(result_node)
    result_node = NULL

    return result


cdef pq_entity* heappq_pop_max(heappq* pq):
    if pq.max_node == NULL:
        return NULL

    pq.size -= 1

    cdef pq_node* result_node = pq.max_node
    cdef pq_node* parent_node = result_node.parent
    cdef pq_node* child_node = result_node.child
    cdef pq_node* left_node = result_node.left

    if child_node != NULL:
        if child_node.child != NULL:
            child_node.child.parent = pq.max_node
        result_node = child_node
        pq.max_node.child = result_node.child


    elif left_node == NULL:
        if parent_node != NULL:
            parent_node.right = NULL
            pq.max_node = parent_node
        else:
            pq.root = NULL
            pq.min_node = NULL
            pq.max_node = NULL

    else:
        if parent_node == NULL:
            left_node.parent = NULL
            pq.root = left_node
        else:
            result_node.left = NULL
            left_node.parent = parent_node
            parent_node.right = left_node

        pq.max_node = left_node
        while pq.max_node.right != NULL:
            pq.max_node = pq.max_node.right
        pq.max_node.right = NULL

    cdef pq_entity* result = result_node.entity
    result_node.entity = NULL
    result_node.left = NULL
    result_node.right = NULL
    result_node.parent = NULL
    result_node.child = NULL
    PyMem_Free(result_node)

    return result


cdef pq_entity* heappq_peak_min(heappq* pq):
     if pq.min_node == NULL:
         return NULL
     return pq.min_node.entity

cdef pq_entity* heappq_peak_max(heappq* pq):
    if pq.max_node == NULL:
        return NULL
    return pq.max_node.entity

cdef inline object fromvoidptr(void *a):
     cdef cpython.PyObject *o
     o = <cpython.PyObject *> a
     cpython.Py_XINCREF(o)
     return <object> o



cdef class PriorityQueue(object):
    cdef heappq* pq

    def __init__(self):
        self.pq = init_heappq()

    def push(self, priority, item):
        heappq_push(self.pq, priority, <void*> item)

    def peak_min(self):
        cdef pq_entity* e = heappq_peak_min(self.pq)
        if e == NULL:
            return (None, None)

        return (e.priority, fromvoidptr(e.value))

    def peak_max(self):
        cdef pq_entity* e = heappq_peak_max(self.pq)
        if e == NULL:
            return (None, None)

        return (e.priority, fromvoidptr(e.value))

    def is_empty(self):
        return self.pq.size == 0

    def pop_min(self):
        cdef pq_entity* e = heappq_pop_min(self.pq)
        if e == NULL:
            return (None, None)

        cdef object o = fromvoidptr(e.value)
        cdef float p = e.priority
        PyMem_Free(e)

        return (p, o)

    def pop_max(self):
        cdef pq_entity* e = heappq_pop_max(self.pq)
        if e == NULL:
            return (None, None)
        cdef object o = fromvoidptr(e.value)
        cdef float p = e.priority
        PyMem_Free(e)

        return (p, o)

    @property
    def size(self):
        return self.pq.size

    def __dealloc__(self):
        free_heappq(self.pq)

    def free(self):
        free_heappq(self.pq)
