import faiss
import numpy as np


class PCAMix:
    def __init__(self, m: int = 1, top_n: int = 200):
        self.m = m
        self.top_n = top_n
        if self.top_n % m != 0:
            raise ValueError('Incorrect top_n')
        self.bytes = int(self.top_n / self.m)

        self.components = []
        self.mean = []

    def train(self, vecs: np.ndarray, save_path: str = None) -> None:
        n = vecs.shape[1]
        pca = faiss.PCAMatrix(n, self.top_n)
        mean = np.mean(vecs, axis=0)
        pca.train(vecs)
        explained_variance_ratio = faiss.vector_to_array(pca.eigenvalues)
        explained_variance_ratio = explained_variance_ratio[:self.top_n]
        components = faiss.vector_to_array(pca.PCAMat).reshape(
            [n, n])[:self.top_n]

        # permutate engive according to variance
        max_entropy = 0
        opt_order = None
        for _ in range(100000):
            tmp = list(range(self.top_n))
            np.random.shuffle(tmp)
            tmp_ratio = np.reshape(explained_variance_ratio[tmp],
                                   [self.bytes, self.m])
            tmp_ratio = np.sum(tmp_ratio, axis=1)
            entropy = -np.sum(tmp_ratio * np.log(tmp_ratio))
            if entropy > max_entropy:
                opt_order = tmp
                max_entropy = entropy
        comp_tmp = np.reshape(components[opt_order], [self.top_n, n])

        self.mean = mean
        self.components = np.transpose(comp_tmp)
        if save_path:
            self.save(save_path)

    def transform(self, vecs: np.ndarray) -> np.ndarray:
        return np.matmul(vecs - self.mean, self.components)
