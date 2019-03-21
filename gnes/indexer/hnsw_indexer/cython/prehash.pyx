# cython: language_level=3

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
cimport cpython

cdef unsigned int BUCKET_CAPACITY = 10000

cdef _bucket* _new_bucket(unsigned int capacity, unsigned int offset):
    cdef _bucket* bucket = <_bucket*> PyMem_Malloc(sizeof(_bucket))
    cdef unsigned int _0
    bucket.values = <value_t*> PyMem_Malloc(sizeof(value_t)*capacity)
    for _0 in range(capacity):
        bucket.values[_0] = NULL
    bucket.capacity = capacity
    bucket.offset = offset
    bucket.size = 0

    return bucket

cdef void _bucket_insert(_bucket* bucket, key_t id, value_t value):
    if bucket.values[id] == NULL:
        bucket.size += 1
    bucket.values[id] = value


cdef value_t _bucket_get(_bucket* bucket, key_t id):
    return bucket.values[id]

cdef void _bucket_delete(_bucket* bucket, key_t id):
    if bucket.values[id] != NULL:
        bucket.values[id] = NULL
        bucket.size -= 1

cdef void _bucket_free(_bucket* bucket):
    cdef key_t _0
    for _0 in range(bucket.capacity):
        _bucket_delete(bucket, _0)

    PyMem_Free(bucket.values)
    bucket.values = NULL
    bucket.offset = 0
    bucket.size = 0
    PyMem_Free(bucket)


cdef prehash_map* init_prehash_map():
    cdef prehash_map* map = <prehash_map*> PyMem_Malloc(sizeof(prehash_map))
    map.total_size = 0

    map.buckets = <_bucket**> PyMem_Malloc(sizeof(_bucket*))
    map.buckets[0] = _new_bucket(BUCKET_CAPACITY, 0)
    map.bucket_count = 1

    return map


cdef void prehash_insert(prehash_map* map, key_t id, value_t value):
     cdef unsigned int bucket_id = _get_bucket_id(id, BUCKET_CAPACITY)
     cdef unsigned int offset = id - bucket_id*BUCKET_CAPACITY

     cdef unsigned int _0 = map.bucket_count

     if bucket_id >= map.bucket_count:
         map.buckets = <_bucket**> PyMem_Realloc(map.buckets, sizeof(_bucket*) * (bucket_id+1))
         map.bucket_count = bucket_id+1
         while _0 < map.bucket_count:
             map.buckets[_0] = _new_bucket(BUCKET_CAPACITY, BUCKET_CAPACITY*_0)
             _0 += 1

     cdef _bucket* bucket = map.buckets[bucket_id]

     _bucket_insert(bucket, offset, value)
     map.total_size += 1

cdef value_t prehash_get(prehash_map* map, key_t id):
    cdef unsigned int bucket_id = _get_bucket_id(id, BUCKET_CAPACITY)
    cdef unsigned int offset = id - BUCKET_CAPACITY*bucket_id
    if bucket_id >= map.bucket_count:
        return NULL
    cdef _bucket* bucket = map.buckets[bucket_id]
    return _bucket_get(bucket, offset)

cdef void prehash_delete(prehash_map* map, key_t id):
    cdef unsigned int bucket_id = _get_bucket_id(id, BUCKET_CAPACITY)
    cdef unsigned int offset = id - BUCKET_CAPACITY*bucket_id
    if bucket_id >= map.bucket_count:
        return

    cdef _bucket* bucket = map.buckets[bucket_id]
    _bucket_delete(bucket, offset)
    map.total_size -= 1

cdef bint prehash_exist(prehash_map* map, key_t id):
    return prehash_get(map, id) != NULL


cdef bint prehash_is_empty(prehash_map* map):
    return map.total_size == 0


cdef unsigned int _get_bucket_id(unsigned int id, unsigned int capacity):
    cdef unsigned int i = int(id / capacity)
    return i

cdef key_t prehash_max_index(prehash_map* map):
    return map.bucket_count * BUCKET_CAPACITY

cdef void prehash_free(prehash_map* map):
    cdef unsigned int i
    cdef _bucket* bucket
    for i in range(map.bucket_count):
        bucket = map.buckets[i]
        if bucket != NULL:
            _bucket_free(bucket)
            map.buckets[i] = NULL
    PyMem_Free(map.buckets)
    map.buckets = NULL
    PyMem_Free(map)

cdef inline object fromvoidptr(void *a):
     cdef cpython.PyObject *o
     o = <cpython.PyObject *> a
     cpython.Py_XINCREF(o)
     return <object> o


cdef class PrehashMap(object):
    cdef prehash_map* _map_ptr

    def __cinit__(self):
        self._map_ptr = init_prehash_map()

    def insert(self, id, data):
        prehash_insert(self._map_ptr, id, <void*> data)

    def get(self, id):
        # return fromvoidptr(prehash_get(self._map_ptr, id))
        cdef value_t value = prehash_get(self._map_ptr, id)
        if value == NULL:
            return None

        return <object> <void*> value

    def delete(self, id):
        prehash_delete(self._map_ptr, id)

    def is_empty(self):
        return prehash_is_empty(self._map_ptr)

    def exist(self, id):
        return prehash_exist(self._map_ptr, id)

    @property
    def size(self):
        return self._map_ptr.total_size

    def __dealloc__(self):
        prehash_free(self._map_ptr)