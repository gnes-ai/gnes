# cython: language_level=3

# pylint: disable=low-comment-ratio, missing-license

#  Tencent is pleased to support the open source community by making GNES available.
#
#  Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.
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

# pylint: disable=low-comment-ratio


ctypedef void*queue_value

cdef struct queue_entry:
    queue_value data
    queue_entry *prev
    queue_entry *next

cdef struct queue:
    queue_entry *head
    queue_entry *tail
    unsigned int size

cdef queue*init_queue()

cdef void queue_free(queue*q_ptr)

cdef void queue_push_head(queue*q_ptr, queue_value data)

cdef queue_value queue_pop_head(queue*q_ptr)

cdef queue_value queue_peak_head(queue*q_ptr)

cdef void queue_push_tail(queue*q_ptr, queue_value data)

cdef queue_value queue_pop_tail(queue*q_ptr)

cdef queue_value queue_peak_tail(queue*q_ptr)

cdef bint queue_is_empty(queue*q_ptr)
