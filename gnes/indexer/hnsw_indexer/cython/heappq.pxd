# cython: language_level=3

# pylint: disable=low-comment-ratio, missing-license

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
