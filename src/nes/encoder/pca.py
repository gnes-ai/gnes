import faiss
import numpy as np

from . import BaseEncoder as BE


class PCAMixEncoder(BE):
    def __init__(self, dim_per_byte: int = 1, num_components: int = 200, model_path: str = None):
        super().__init__(model_path)
        self.dim_per_byte = dim_per_byte
        self.principle_dim = num_components
        if self.principle_dim % dim_per_byte != 0:
            raise ValueError('Bad value of "m" and "top_n", "top_n" must be dividable by "m"! '
                             'Received m=%d and top_n=%d.' % (dim_per_byte, num_components))
        self.bytes = int(self.principle_dim / self.dim_per_byte)

        self.components = []
        self.mean = []

    @BE.as_train_func
    def train(self, vecs: np.ndarray) -> None:
        n = vecs.shape[1]
        pca = faiss.PCAMatrix(n, self.principle_dim)
        self.mean = np.mean(vecs, axis=0)  # 1 x 768
        pca.train(vecs)
        explained_variance_ratio = faiss.vector_to_array(pca.eigenvalues)[:self.principle_dim]
        components = faiss.vector_to_array(pca.PCAMat).reshape([n, n])[:self.principle_dim]

        # permutate engive according to variance
        max_entropy = -9999
        normalizer = np.sum(explained_variance_ratio)
        opt_order = None  # top_n_dim, 200
        for _ in range(100000):
            tmp = list(range(self.principle_dim))
            np.random.shuffle(tmp)
            tmp_ratio = np.reshape(explained_variance_ratio[tmp], [self.bytes, self.dim_per_byte])
            tmp_ratio = np.sum(tmp_ratio, axis=1) / normalizer
            entropy = -np.sum(tmp_ratio * np.log(tmp_ratio))
            if entropy > max_entropy:
                opt_order = tmp
                max_entropy = entropy
        comp_tmp = np.reshape(components[opt_order], [self.principle_dim, n])

        self.components = np.transpose(comp_tmp)  # 768 x 200

    @BE.train_required
    def encode(self, vecs: np.ndarray, **kwargs) -> np.ndarray:
        return np.matmul(vecs - self.mean, self.components)
