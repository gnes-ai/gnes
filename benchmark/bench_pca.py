import numpy as np
from memory_profiler import memory_usage
from src.nes.encoder.pca import PCALocalEncoder


def pca_test(vecs, output_dim, output_locals):
    pca = PCALocalEncoder(output_dim, output_locals)
    pca.train(vecs)


def test_input_dim():
    for n in [1000, 10000, 100000, 1000000]:
        vecs = np.random.random([n, 768]).astype(np.float32)
        mem = memory_usage((pca_test, (vecs, 200, 20)))
        print('{} lines, time {}, RAM usage {}'.format(n, len(mem)/10, max(mem)))


def test_output_dim():
    vecs = np.random.random([10000, 768]).astype(np.float32)
    for out in [20, 50, 100, 200, 300, 500, 760]:
        mem = memory_usage((pca_test, (vecs, out, 10)))
        print('{} output dim, time {}, RAM usage {}'.format(out, len(mem)/10, max(mem)))


if __name__ == '__main__':
    test_input_dim()
    test_output_dim()
