import faiss
import numpy as np

from . import BaseEncoder
from ..base import TrainableBase as TB
from ..helper import get_perm, get_sys_info, ralloc_estimator


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

    @TB._timeit
    def train(self, vecs: np.ndarray, *args, **kwargs) -> None:
        num_samples, num_dim = vecs.shape
        assert self.output_dim <= num_samples, 'training PCA requires at least %d points, but %d was given' % (
            self.output_dim, num_samples)
        assert self.output_dim < num_dim, 'PCA output dimension should < data dimension, received (%d, %d)' % (
            self.output_dim, num_dim)

        pca = faiss.PCAMatrix(num_dim, self.output_dim)
        self.mean = np.mean(vecs, axis=0)  # 1 x 768
        max_mem, unit_time = get_sys_info()
        optimal_num_samples = ralloc_estimator(num_samples, num_dim, unit_time,
                                               max_mem, 30)
        pca.train(vecs[:optimal_num_samples])
        explained_variance_ratio = faiss.vector_to_array(pca.eigenvalues)[:self.output_dim]
        components = faiss.vector_to_array(pca.PCAMat).reshape([-1, num_dim])[:self.output_dim]

        # permutate engive according to variance
        opt_order = get_perm(explained_variance_ratio, self.num_locals)
        comp_tmp = np.reshape(components[opt_order], [self.output_dim, num_dim])

        self.components = np.transpose(comp_tmp)  # 768 x 200

    @TB._train_required
    @TB._timeit
    def encode(self, vecs: np.ndarray, *args, **kwargs) -> np.ndarray:
        if vecs.shape[0] < 2048:
            return np.matmul(vecs - self.mean, self.components)
        else:
            ret = None
            for _ in range(int(vecs.shape[0]/2048)+1):
                if _ * 2048 < vecs.shape[1]:
                    _r = np.matmul(vecs - self.mean, self.components)
                    ret = np.concatenate([ret, _r]) if ret is not None else _r
            return ret

    def _copy_from(self, x: 'PCALocalEncoder') -> None:
        self.output_dim = x.output_dim
        self.components = x.components
        self.mean = x.mean
        self.num_locals = x.num_locals
        self.is_trained = x.is_trained
