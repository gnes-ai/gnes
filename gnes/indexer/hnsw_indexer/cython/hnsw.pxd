# cython: language_level=3

ctypedef float DIST
ctypedef unsigned int UINT
ctypedef unsigned short USHORT
ctypedef unsigned char UCHAR
ctypedef UCHAR* BVECTOR
ctypedef unsigned int UIDX

cdef struct hnsw_edge:
    hnswNode* node
    DIST dist
    hnsw_edge* next

cdef struct hnsw_edge_set:
    hnsw_edge* head_ptr
    hnsw_edge* last_ptr
    UINT size

cdef struct hnswNode:
    UIDX id
    BVECTOR vector
    USHORT level
    hnsw_edge_set** edges
    hnswNode* next
    USHORT in_degree


cdef struct hnswConfig:
    float level_multiplier
    int ef
    int ef_construction
    int m
    int m_max
    int m_max_0
