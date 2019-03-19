import faiss
import numpy as np

from .base import BaseEncoder
from ..base import TrainableBase as TB


class PQEncoder(BaseEncoder):
    def __init__(self, num_bytes: int, cluster_per_byte: int = 255, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert 1 < cluster_per_byte <= 255, 'cluster number should >1 and <= 255 (0 is reserved for NOP)'
        self.num_bytes = num_bytes
        self.num_clusters = cluster_per_byte
        self.centroids = None

    def train(self, vecs: np.ndarray, *args, **kwargs):
        dim_per_byte = self._get_dim_per_byte(vecs)

        # use faiss ProductQuantizer directly
        vecs = vecs.astype(np.float32)
        model = faiss.ProductQuantizer(vecs.shape[1], self.num_bytes, 8)
        model.ksub = self.num_clusters
        model.byte_per_idx = 1

        model.train(vecs)
        centroids = faiss.vector_to_array(model.centroids)
        centroids = centroids[: self.num_clusters * vecs.shape[1]]
        self.centroids = np.reshape(centroids, [1, self.num_bytes,
                                                self.num_clusters,
                                                dim_per_byte])

    @TB._train_required
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        dim_per_byte = self._get_dim_per_byte(vecs)

        x = np.reshape(vecs, [vecs.shape[0], self.num_bytes, 1, dim_per_byte])
        x = np.sum(np.square(x - self.centroids), -1)
        # start from 1
        x = np.argmax(-x, 2) + 1

        return np.array(x, dtype=np.uint8)

    def _get_dim_per_byte(self, vecs: np.ndarray):
        num_dim = vecs.shape[1]
        assert num_dim >= self.num_bytes and num_dim % self.num_bytes == 0, \
            'input dimension should >= num_bytes and can be divided by num_bytes!'
        return int(num_dim / self.num_bytes)

    def _copy_from(self, x: 'PQEncoder') -> None:
        self.num_bytes = x.num_bytes
        self.num_clusters = x.num_clusters
        self.centroids = x.centroids
        self.is_trained = x.is_trained
