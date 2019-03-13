import faiss
import numpy as np

from . import BaseEncoder
from ..base import TrainableBase as TB
from ..helper import get_perm


class PCALocalEncoder(BaseEncoder):
    def __init__(self, output_dim: int, num_locals: int,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert output_dim >= num_locals and output_dim % num_locals == 0, \
            'output_dim should >= num_locals and can be divided by num_locals!'
        self.output_dim = output_dim
        self.num_locals = num_locals
        self.components = None
        self.mean = None

    def train(self, vecs: np.ndarray, *args, **kwargs) -> None:
        num_samples, num_dim = vecs.shape
        assert self.output_dim <= num_samples, 'training PCA requires at least %d points, but %d was given' % (
            self.output_dim, num_samples)
        assert self.output_dim < num_dim, 'PCA output dimension should < data dimension, received (%d, %d)' % (
            self.output_dim, num_dim)

        pca = faiss.PCAMatrix(num_dim, self.output_dim)
        self.mean = np.mean(vecs, axis=0)  # 1 x 768
        pca.train(vecs)
        explained_variance_ratio = faiss.vector_to_array(pca.eigenvalues)[:self.output_dim]
        components = faiss.vector_to_array(pca.PCAMat).reshape([-1, num_dim])[:self.output_dim]

        # permutate engive according to variance
        opt_order = get_perm(explained_variance_ratio, self.num_locals)
        comp_tmp = np.reshape(components[opt_order], [self.output_dim, num_dim])

        self.components = np.transpose(comp_tmp)  # 768 x 200

    @TB._train_required
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        return np.matmul(vecs - self.mean, self.components)

    def _copy_from(self, x: 'PCALocalEncoder') -> None:
        self.output_dim = x.output_dim
        self.components = x.components
        self.mean = x.mean
        self.num_locals = x.num_locals
        self.is_trained = x.is_trained
