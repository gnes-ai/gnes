# How to write your GNES YAML config

YAML is everywhere. This is pretty much your impression when first trying GNES. Understanding the YAML config is therefore extremely important to use GNES.

Essentially, GNES only requires two types of YAML config:
- GNES-compose YAML
- Component-wise YAML

The docker-compose YAML config  and Kubernetes config generated from GNES Board or `$ gnes compose` command is not a part of this tutorial. Interested readers are welcome to read their YAML specification respectively.

## GNES-compose YAML

GNES-compose YAML defines  