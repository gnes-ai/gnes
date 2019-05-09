import numpy as np
from gnes.proto import gnes_pb2


## proto / datum / ndarray conversion
def blob2array(blob: bytes) -> np.ndarray:
    """
    Convert a blob proto to an array.
    """
    return np.frombuffer(blob.data, dtype=blob.dtype).reshape(blob.shape)


def array2blob(x: np.ndarray) -> 'gnes_pb2.Array':
    """Converts a N-dimensional array to blob proto.
    """
    blob = gnes_pb2.Array()
    blob.data = x.tobytes()
    blob.shape.extend(list(x.shape))
    blob.dtype = x.dtype.name
    return blob
