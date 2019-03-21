import numpy as np
from memory_profiler import memory_usage
from gnes.encoder.pq import PQEncoder


def pq_test(vecs, num_bytes, cluster_per_byte):
    pq = PQEncoder(num_bytes, cluster_per_byte)
    pq.train(vecs)


def test_n_samples():
    for dim in [10000, 100000, 1000000, 10000000, 30000000, 50000000]:
        vecs = np.random.random([dim, 200]).astype(np.float32)
        mem = memory_usage((pq_test, (vecs, 20, 200)))
        print('{} lines, time {}, RAM usage {}'.format(dim, len(mem)/10, max(mem)))


def test_n_bytes():
    vecs = np.random.random([1000000, 200]).astype(np.float32)
    for nbytes in [1, 5, 10, 20, 40, 50, 100, 200]:
        mem = memory_usage((pq_test, (vecs, nbytes, 200)))
        print('{} bytes, time {}, RAM usage {}'.format(nbytes, len(mem)/10, max(mem)))


def test_num_clusters():
    vecs = np.random.random([10000, 200]).astype(np.float32)
    for n_clus in [10, 50, 100, 150, 250]:
        mem = memory_usage((pq_test, (vecs, 20, n_clus)))
        print('{} clus, time {}, RAM usage {}'.format(n_clus, len(mem)/10, max(mem)))


if __name__ == '__main__':
    test_n_samples()
    test_n_bytes()
    test_num_clusters()
