# cython: language_level=3

#  Copyright 2019
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from libc.stdint cimport uint64_t

ctypedef uint64_t key_t
ctypedef void*value_t

#cdef struct _cell:
#    key_t key
#    value_t value

cdef struct _bucket:
    value_t*values
    unsigned int capacity
    unsigned int offset
    unsigned int size

cdef struct prehash_map:
    _bucket** buckets
    unsigned int bucket_count
    unsigned int total_size

cdef _bucket*_new_bucket(unsigned int capacity, unsigned int offset)

cdef void _bucket_insert(_bucket*bucket, key_t id, value_t value)

cdef value_t _bucket_get(_bucket*bucket, key_t id)

cdef void _bucket_delete(_bucket*bucket, key_t id)

cdef void _bucket_free(_bucket*bucket)

cdef prehash_map*init_prehash_map()

cdef void prehash_insert(prehash_map*map, key_t id, value_t value)

cdef value_t prehash_get(prehash_map*map, key_t id)

cdef void prehash_delete(prehash_map*map, key_t id)

cdef bint prehash_exist(prehash_map*map, key_t id)

cdef bint prehash_is_empty(prehash_map*map)

cdef void prehash_free(prehash_map*map)

cdef key_t prehash_max_index(prehash_map*map)
