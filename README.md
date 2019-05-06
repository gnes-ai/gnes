<p align="center">
    <img src=".github/gnes-logo-tight.png?raw=true" width="300" alt="GNES Generic Neural Elastic Search, logo made by Han Xiao">
</p>

<p align="center">GNES is Generic Neural Elastic Search, a highly scalable semantic search system based on deep neural network.</p>

<p align="center">
<a href="#">
    <img src="http://badge.orange-ci.oa.com/ai-innersource/nes.svg" alt="building status">
</a>
<a href="https://github.com/hanxiao/bert-as-service/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/tensorflow/tensorflow.svg"
         alt="GitHub license">
</a>
</p>

<p align="center">
  <a href="#highlights">Highlights</a> •
  <a href="#what-is-it">What is it</a> •
  <a href="#install">Install</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#server-and-client-api">API</a> •
  <a href="#book-tutorial">Tutorials</a> •
  <a href="#speech_balloon-faq">FAQ</a>  
</p>



<h2 align="center">Highlights</h2>

- :telescope: **State-of-the-art**: 
- :hatching_chick: **Easy-to-use on every level**: a YAML file is all you need to enable GNES.
- :zap: **Fast**: 
- :octopus: **Scalable**: built on Docker Swarm, GNES can be easily scaled up on multiple CPUs, GPUs and hosts.
- :gem: **Reliable**: serves on billion-level documents and queries; days of running without a break or OOM or any nasty exceptions.


<h2 align="center">Getting Started</h2>

### Using GNES with Docker Swarm

The easiest and the recommended way to use GNES is via Docker, which uses containers to create virtual environments that isolate a GNES installation from the rest of the system. You don't need to worry about dependencies, they are self-contained in the GNES docker image. Moreover, GNES relies on the Docker Swarm for managing, scaling and conducting orchestration tasks over multiple micro-services. 

#### 1. Prerequisites

- [Docker Engine>=1.13](https://docs.docker.com/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Docker Machine](https://docs.docker.com/machine/install-machine/)


#### 2. Start GNES with the wizard

If you are new to GNES, it is recommended to use the wizard to config and start GNES.

```bash
bash <(curl -s https://transfer.sh/yVeBa/gnes-wizard.sh)
```

To stop a running GNES service, you can first use `docker stack ls` to find the name of the running services, say `gnes-swarm-0531`, then do: 
```bash
docker stack rm gnes-swarm-0531
```

<h2 align="center">:book: Documentation</h2>

The official documentation of GNES is hosted on Read the Docs. It is automatically built, updated and archived on every new release. 


### Building the documentation from scratch

To build the documentation by yourself, you need to first [install sphinx](http://www.sphinx-doc.org/en/master/usage/installation.html).

```bash
git clone https://github.com/tencent/gnes.git && cd gnes
sphinx-apidoc -o ./docs/ ./gnes
make html
```

<h2 align="center">Tutorial</h2>

<h2 align="center">Contributing</h2>

<h2 align="center">TODO</h2>

<h2 align="center">Contact</h2>

<h2 align="center">License</h2>

[Apache License 2.0](./LICENSE)