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


from typing import List, Tuple, Dict

# from ..document import BaseDocument, DocumentMapper
from ..encoder.base import CompositionalEncoder, train_required
from ..helper import batching
from ..proto import gnes_pb2


class GNES(CompositionalEncoder):
    def train(self, lst_doc: List['gnes_pb2.Document'], *args, **kwargs) -> None:
        # sents = DocumentMapper(lst_doc).sent_id_sentence[1]
        chunks = []
        for doc in lst_doc:
            for chunk in doc.chunks:
                if chunk.HasField("text"):
                    chunks.append(chunk.text)
                elif chunk.HasField("blob"):
                    chunks.append(chunk.blob)
                else:
                    raise ValueError("the chunk has empty content")

        self.component['encoder'].train(chunks, *args, **kwargs)

    @train_required
    @batching
    def add(self, lst_doc: List['gnes_pb2.Document'], *args, **kwargs) -> None:
        chunks = []
        doc_keys = []
        doc_ids = []
        for doc in lst_doc:
            doc_ids.add(doc.id)
            for i, chunk in enumerate(doc.chunks):
                if chunk.HasField("text"):
                    chunks.append(chunk.text)
                elif chunk.HasField("blob"):
                    chunks.append(chunk.blob)
                else:
                    raise ValueError("the chunk has empty content")
                doc_keys.append((doc.id, i))

        bin_vectors = self.component['encoder'].encode(chunks, *args, **kwargs)
        i = 0
        for doc in lst_doc:
            for chunk in doc.chunks:
                chunk.encode = bin_vectors[i]
                i += 1

        self.component['binary_indexer'].add(doc_keys, bin_vectors)
        self.component['doc_indexer'].add(doc_ids, lst_doc)

    @train_required
    def query(self, keys: List[str], top_k: int, *args, **kwargs) -> List[List[Tuple[Dict, float]]]:
        bin_queries = self.component['encoder'].encode(keys, *args, **kwargs)

        result_score = self.component['binary_indexer'].query(bin_queries, top_k)

        all_ids = list(set(d[0] for id_score in result_score for d in id_score if d[0] >= 0))
        result_doc = self.component['text_indexer'].query(all_ids)
        id2doc = {d_id: d_content for d_id, d_content in zip(all_ids, result_doc)}
        return [[(id2doc[d_id], d_score) for d_id, d_score in id_score] for id_score in result_score]
