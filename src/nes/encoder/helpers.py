import argparse
import numpy as np
import pickle


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


def pdumps(obj, data_path):
    with open(data_path, 'wb') as f:
        pickle.dump(obj, f)
    return True


def ploads(data_path):
    with open(data_path, 'rb') as f:
        obj = pickle.load(f)
    return obj
