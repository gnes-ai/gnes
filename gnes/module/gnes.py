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

from typing import List, Tuple, Dict, Any

from ..encoder.base import CompositionalEncoder
from ..helper import batching, train_required
from ..proto import gnes_pb2, array2blob


class GNES(CompositionalEncoder):

    def train(self, lst_doc: List['gnes_pb2.Document'], *args,
              **kwargs) -> None:
        # sents = DocumentMapper(lst_doc).sent_id_sentence[1]
        chunks = []
        for doc in lst_doc:
            if doc.doc_type == gnes_pb2.Document.TEXT_DOC:
                chunks.extend(doc.text_chunks)
            elif doc.doc_type == gnes_pb2.Document.IMAGE_DOC:
                chunks.extend(doc.blob_chunks)
            else:
                raise NotImplemented()

        self.component['encoder'].train(chunks, *args, **kwargs)

    @train_required
    @batching
    def add(self, lst_doc: List['gnes_pb2.Document'], *args, **kwargs) -> None:
        chunks = []
        doc_keys = []
        doc_ids = []
        for doc in lst_doc:
            doc_ids.append(doc.id)
            doc_chunks = doc.text_chunks if len(
                doc.text_chunks) > 0 else doc.blob_chunks
            for i, chunk in enumerate(doc_chunks):
                chunks.append(chunk)
                doc_keys.append((doc.id, i))

        bin_vectors = self.component['encoder'].encode(chunks, *args, **kwargs)
        doc.encodes.CopyFrom(array2blob(bin_vectors))

        self.component['binary_indexer'].add(doc_keys, bin_vectors)
        self.component['doc_indexer'].add(doc_ids, lst_doc)

    @train_required
    def query(self, keys: List[Any], top_k: int, *args,
              **kwargs) -> List[List[Tuple[Dict, float]]]:
        bin_queries = self.component['encoder'].encode(keys, *args, **kwargs)

        topk_results = self.component['binary_indexer'].query(
            bin_queries, top_k)

        doc_caches = dict()
        results = []
        for topk in topk_results:
            result = []
            for key, score in topk:
                doc_id, offset = key
                doc = doc_caches.get(doc_id, None)
                if doc is None:
                    doc = self.component['doc_indexer'].query([doc_id])[0]
                    doc_caches[doc_id] = doc

                chunk = doc.text_chunks[
                    offset] if doc.text_chunks else doc.blob_chunks[offset]
                result.append(({
                                   "doc_id": doc_id,
                                   "doc_size": doc.doc_size,
                                   "offset": offset,
                                   "chunk": chunk
                               }, score))
            results.append(result)

        return results
