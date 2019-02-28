import faiss
import numpy as np

from . import BaseEncoder as BE
from ..helper import get_perm


class PCALocalEncoder(BE):
    def __init__(self, output_dim: int, num_locals: int):
        super().__init__()
        assert output_dim % num_locals == 0, \
            'output_dim %d is not divided by num_subspaces %d' % (output_dim, num_locals)
        self.output_dim = output_dim
        self.num_locals = num_locals
        self.components = None
        self.mean = None

    @BE._as_train_func
    def train(self, vecs: np.ndarray) -> None:
        n = vecs.shape[1]
        pca = faiss.PCAMatrix(n, self.output_dim)
        self.mean = np.mean(vecs, axis=0)  # 1 x 768
        pca.train(vecs)
        explained_variance_ratio = faiss.vector_to_array(pca.eigenvalues)[:self.output_dim]
        components = faiss.vector_to_array(pca.PCAMat).reshape([n, n])[:self.output_dim]

        # permutate engive according to variance
        opt_order = get_perm(explained_variance_ratio, self.num_locals)
        comp_tmp = np.reshape(components[opt_order], [self.output_dim, n])

        self.components = np.transpose(comp_tmp)  # 768 x 200

    @BE._train_required
    def encode(self, vecs: np.ndarray) -> np.ndarray:
        return np.matmul(vecs - self.mean, self.components)

    def copy_from(self, x: 'PCALocalEncoder'):
        self.output_dim = x.output_dim
        self.components = x.components
        self.mean = x.mean
        self.num_locals = x.num_locals
        self.is_trained = x.is_trained
