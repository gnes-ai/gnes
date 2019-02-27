import argparse
import pickle
from typing import Any

import numpy as np


def parse_args():
    parser = argparse.ArgumentParser('Arguments for OPQ')

    parser.add_argument('--k', type=int, default=200,
                        help='num dimensions per vector')
    parser.add_argument('--m', type=int, default=20,
                        help='num dimensions per bytes')
    parser.add_argument('--num_clusters', type=int, default=100,
                        help='num dimensions per bytes')
    parser.add_argument('--vecs_path', type=str,
                        default='./data/vecs.txt.mini')

    parser.add_argument('--params_path', type=str,
                        default='./data/lopq_params.pkl',
                        help='params pickle path')

    parser.add_argument('--pred_path', type=str,
                        default='./data/pred.bin')
    return parser.parse_args()


def read_vecs(data_path):
    vecs = np.loadtxt(data_path, dtype=np.float32, delimiter=' ')
    return vecs


def save_vecs(data_path, vecs):
    with open(data_path, 'w') as f:
        np.savetxt(f, vecs, fmt='%2.3f')


def pdumps(obj: Any, data_path: str):
    with open(data_path, 'wb') as f:
        pickle.dump(obj, f)


def ploads(data_path: str) -> Any:
    with open(data_path, 'rb') as f:
        return pickle.load(f)


def get_perm(L, m):
    n = int(len(L) / m)
    avg = sum(L) / len(L) * m
    LR = sorted(enumerate(L), key=lambda x: -x[1])
    L = np.reshape([i[1] for i in LR], [m, n])
    R = np.reshape([i[0] for i in LR], [m, n])
    F = np.zeros([m, n])

    reranked = []
    ind = 0
    for _ in range(n):
        for i in range(m):
            if i % 2 == 0:
                start, direction = 0, 1
            else:
                start, direction = n-1, -1
            while F[i, start] == 1:
                start += direction
            if (ind + L[i, start] < avg) or (direction == 1):
                ind += L[i, start]
                F[i, start] = 1
                reranked.append(R[i, start])
            else:
                start, direction = n-1, -1
                while F[i, start] == 1:
                    start += direction
                ind += L[i, start]
                F[i, start] = 1
                reranked.append(R[i, start])

    return reranked
