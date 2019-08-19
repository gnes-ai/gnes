# YAML Config Explained

A typical GNES configuration contains multiple YAML files, such as:

```bash
index-compose.yml
query-compose.yml
train-compose.yml
indexer.yml
encoder.yml
```

Together they define the behavior of a GNES system. Roughly speaking, 

- `encoder.yml` defines an encoder component;
- `indexer.yml` defines an indexer component;
- `*-compose.yml` defines how components work together in index/query/train mode.

## `encoder.yml`

`encoder.yml` defines an encoder: how it is composed, what are the parameters. In the example below, we define a simple pipeline encoder using word2vec and PCA. 
 
```yaml
!PipelineEncoder
components:
  - !Word2VecEncoder
    parameters:
      model_dir: /ext_data/sgns.wiki.bigram-char.refine
    property:
      is_trained: true
  - !PCALocalEncoder
    parameters:
      output_dim: 200
      num_locals: 10
    property:
      batch_size: 2048
```

One can also append extra component to this pipeline, e.g. adding quantization.

```yaml
!PipelineEncoder
components:
  - !Word2VecEncoder
    parameters:
      model_dir: /ext_data/sgns.wiki.bigram-char.refine
    property:
      is_trained: true
  - !PCALocalEncoder
    parameters:
      output_dim: 200
      num_locals: 10
    property:
      batch_size: 2048
  - !PQEncoder
    parameters:
      cluster_per_byte: 20
      num_bytes: 10
```



