# cython: language_level=3
from libc.stdint cimport uint64_t

ctypedef uint64_t key_t
ctypedef void* value_t

#cdef struct _cell:
#    key_t key
#    value_t value

cdef struct _bucket:
    value_t* values
    unsigned int capacity
    unsigned int offset
    unsigned int size


cdef struct prehash_map:
    _bucket** buckets
    unsigned int bucket_count
    unsigned int total_size

cdef _bucket* _new_bucket(unsigned int capacity, unsigned int offset)

cdef void _bucket_insert(_bucket* bucket, key_t id, value_t value)

cdef value_t _bucket_get(_bucket* bucket, key_t id)

cdef void _bucket_delete(_bucket* bucket, key_t id)

cdef void _bucket_free(_bucket* bucket)

cdef prehash_map* init_prehash_map()

cdef void prehash_insert(prehash_map* map, key_t id, value_t value)

cdef value_t prehash_get(prehash_map* map, key_t id)

cdef void prehash_delete(prehash_map* map, key_t id)

cdef bint prehash_exist(prehash_map* map, key_t id)

cdef bint prehash_is_empty(prehash_map* map)

cdef void prehash_free(prehash_map* map)

cdef key_t prehash_max_index(prehash_map* map)