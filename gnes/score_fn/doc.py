from .base import get_unary_score, ScoreCombinedFn


class WeightedDocScoreFn(ScoreCombinedFn):
    def __call__(self, last_score: 'gnes_pb2.Response.QueryResponse.ScoredResult.Score',
                 doc: 'gnes_pb2.Document', *args, **kwargs):
        d_weight = get_unary_score(value=doc.weight,
                                   name='doc weight',
                                   doc_id=doc.doc_id)
        return super().__call__(last_score, d_weight)
