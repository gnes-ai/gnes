<p align="center">
<a href="https://gnes.ai">
    <img src=".github/gnes-github-banner.png?raw=true" alt="GNES Generic Neural Elastic Search, logo made by Han Xiao">
</a>
</p>

<p align="center">
<a href="https://cloud.drone.io/gnes-ai/gnes">
    <img src="https://cloud.drone.io/api/badges/gnes-ai/gnes/status.svg" />
</a>
<a href="https://pypi.org/project/gnes/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/gnes.svg">
</a>
<a href="https://cloud.docker.com/u/gnes/">
    <img alt="Docker Cloud Build Status" src="https://img.shields.io/docker/cloud/build/gnes/gnes.svg">
</a>
<a href='https://doc.gnes.ai/'>
    <img src='https://readthedocs.org/projects/gnes/badge/?version=latest' alt='Documentation Status' />
</a>
<a href="https://www.codacy.com/app/gnes-ai/gnes?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=gnes-ai/gnes&amp;utm_campaign=Badge_Grade">
    <img src="https://api.codacy.com/project/badge/Grade/a9ce545b9f3846ba954bcd449e090984"/>
</a>
<a href="https://codecov.io/gh/gnes-ai/gnes">
  <img src="https://codecov.io/gh/gnes-ai/gnes/branch/master/graph/badge.svg" />
</a>
<a href='https://github.com/gnes-ai/gnes/blob/master/LICENSE'>
    <img alt="PyPI - License" src="https://img.shields.io/pypi/l/gnes.svg">
</a>
</p>

<p align="center">
  <a href="#highlights">Highlights</a> •
  <a href="#overview">Overview</a> •
  <a href="#install-gnes">Install</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#tutorial">Tutorial</a> •
  <a href="#contributing">Contributing</a> •
  <a href="./CHANGELOG.md">Release Notes</a>  
</p>

<h2 align="center">What is it</h2>

GNES [<i>jee-nes</i>] is **Generic Neural Elastic Search**, a cloud-native semantic search system based on deep neural network. 


GNES enables large-scale index and semantic search for text-to-text, image-to-image, video-to-video and possibly any-to-any content form.


<h2 align="center">Highlights</h2>
<center>
<table>
  <tr>
    <th><h3>☁️</h3><h3>Cloud-Native & Elastic</h3></th>
    <th><h3>🐣</h3><h3>Easy-to-Use</h3></th>
    <th><h3>🔬</h3><h3>State-of-the-Art</h3></th>
  </tr>
  <tr>
    <td width="33%"><sub>GNES is <i>all-in-microservice</i>! Encoder, indexer, preprocessor and router are all running in their own containers. They communicate via versioned APIs and collaborate under the orchestration of Docker Swarm/Kubernetes etc. Scaling, load-balancing, automated recovering, they come off-the-shelf in GNES.</sub></td>
    <td width="33%"><sub>How long would it take to deploy a change that involves just switching a layer in VGG? In GNES, this is just one line change in a YAML file. We abstract the encoding and indexing logic to a YAML config, so that you can change or stack encoders and indexers without even touching the codebase.</sub></td>
    <td width="33%"><sub>Taking advantage of fast-evolving AI/ML/NLP/CV communities, we learn from best-of-breed deep learning models and plug them into GNES, making sure you always enjoy the state-of-the-art performance.</sub></td>
  </tr>
  <tr>
      <th><h3>🌌</h3><h3>Generic & Universal</h3></th>
      <th><h3>📦</h3><h3>Model as Plugin</h3></th>
      <th><h3>💯</h3><h3>Best Practice</h3></th>
    </tr>
    <tr>
      <td width="33%"><sub>Searching for texts, image or even short-videos? Using Python/C/Java/Go/HTTP as the client? Doesn't matter which content form you have or which language do you use, GNES can handle them all. </sub></td>
      <td width="33%"><sub>When built-in models do not meet your requirments, simply build your own with <i>one Python file and one YAML file</i>. No need to rebuilt GNES framework, as your models will be loaded as plugins and directly rollout online.</sub></td>
      <td width="33%"><sub>We love to learn the best practice from the community, helping our GNES to achieve the next level of availability, resiliency, performance, and durability. If you have any ideas or suggestions, feel free to contribute.</sub></td>
    </tr>
</table>
</center>

<h2 align="center">Overview</h2>
<p align="center">
<img src=".github/gnes-component-overview.svg" alt="component overview">
</p>

<h2 align="center">Install GNES</h2>

There are two ways to get GNES, either as a Docker image or as a PyPi package.
 
✅ For cloud users, we **highly recommend using GNES via Docker image**. 

### Run GNES as a Docker Container

We provide GNES as a Docker image to simplify the installation. The Docker image is built with GNES full dependencies, so you can run GNES out-of-the-box.

#### via [Docker cloud](https://cloud.docker.com/u/gnes/repository/list)

```bash
docker run gnes/gnes:latest
```

This command downloads the latest GNES image and runs it in a container. When the container runs, it prints an informational message and exits.

#### via Tencent container service

We also provide a public mirror hosted on Tencent Cloud, from which Chinese mainland users can pull the image faster.

```bash
docker login --username=xxx ccr.ccs.tencentyun.com  # login to Tencent Cloud so that we can pull from it
docker run ccr.ccs.tencentyun.com/gnes/gnes:latest
```

> 💡 Please note that version `latest` refers to the latest master of this repository, which is [mutable and may not always be a stable](./CONTRIBUTING.md#Merging-Process). Therefore, we recommend you to use an official release by changing the `latest` to a version tag, say `v0.0.24`.

### Install GNES via `pip`

You can also install GNES as a Python package via:
```bash
pip install gnes
```

Note that this will only install a *"barebone"* version of GNES, consists of **the minimal dependencies** for running GNES, i.e. *no third-party pretrained models, deep learning/NLP/CV packages are installed*. We make this setup as the default installation behavior as in GNES models serve as plugins, and a model interested to NLP engineers may not be interested to CV engineers.

To enable the full functionalities and dependencies, you may install GNES via:
```bash
pip install gnes[all]
```

🍒 Or cherry-picking the dependencies according to the table below:

<details>
 <summary>List of cherry-picked dependencies (click to expand...)</summary>


<table>
<tr><td><pre>pip install gnes[bert]</pre></td><td>bert-serving-server>=1.8.6, bert-serving-client>=1.8.6</td>
<tr><td><pre>pip install gnes[flair]</pre></td><td>flair>=0.4.1</td>
<tr><td><pre>pip install gnes[annoy]</pre></td><td>annoy==1.15.2</td>
<tr><td><pre>pip install gnes[chinese]</pre></td><td>jieba</td>
<tr><td><pre>pip install gnes[vision]</pre></td><td>opencv-python>=4.0.0, torchvision==0.3.0, imagehash>=4.0</td>
<tr><td><pre>pip install gnes[leveldb]</pre></td><td>plyvel>=1.0.5</td>
<tr><td><pre>pip install gnes[test]</pre></td><td>pylint, memory_profiler>=0.55.0, psutil>=5.6.1, gputil>=1.4.0</td>
<tr><td><pre>pip install gnes[http]</pre></td><td>flask, flask-compress, flask-cors, flask-json, aiohttp==3.5.4</td>
<tr><td><pre>pip install gnes[nlp]</pre></td><td>flair>=0.4.1, bert-serving-client>=1.8.6, bert-serving-server>=1.8.6</td>
<tr><td><pre>pip install gnes[cn_nlp]</pre></td><td>bert-serving-server>=1.8.6, bert-serving-client>=1.8.6, jieba, flair>=0.4.1</td>
<tr><td><pre>pip install gnes[all]</pre></td><td>bert-serving-client>=1.8.6, bert-serving-server>=1.8.6, imagehash>=4.0, gputil>=1.4.0, flask, flask-cors, flask-compress, jieba, flair>=0.4.1, opencv-python>=4.0.0, torchvision==0.3.0, pylint, aiohttp==3.5.4, psutil>=5.6.1, flask-json, plyvel>=1.0.5, annoy==1.15.2, memory_profiler>=0.55.0</td>
</table>
</details>


Either way, if you see the following message after `$ gnes` or `$ docker run gnes/gnes`, then you are ready to go!

<p align="center">
<img src=".github/install-success.svg" alt="success installation of GNES">
</p>


<h2 align="center">Quick Start</h2>

### Preliminaries

Before we start, let me first introduce two basic concepts serving as the backbone of GNES: **microservice** and **runtime**. 

#### Microservice

For machine learning engineers and data scientists who are not familiar with the concept of *cloud-native* and *microservice*, one can picture a microservice as an app (on your smartphone). Each app runs independently, and an app may cooperate with other apps to accomplish a task. In GNES, we have four fundamental apps, aka. microservices, they are:

- **Preprocessor**: transforming a real-world object to a list of workable semantic units;
- **Encoder**: representing a semantic unit with vector representation;
- **Indexer**: storing the vectors into memory/disk that allows fast-access;
- **Router**: forwarding messages between microservices: e.g. batching, mapping, reducing.

In GNES, we have implemented dozens of preprocessor, encoder, indexer to process different content forms, such as image, text, video. It is also super easy to plug in your own implementation, which we shall see an example in the sequel.

#### Runtime

Okay, now that we have a bunch of apps, what are we expecting them to do? In a typical search system, there are two fundamental tasks: **indexing** and **querying**. Indexing is storing the documents, querying is searching the documents, pretty straightforward. In a neural search system, one may also face another task: **training**, where one fine-tunes an encoder/preprocessor according to the data distribution in order to achieve better search relevance. These three tasks: indexing, querying and training are what we call three **runtimes** in GNES.

💡 The key to understand GNES is to know *which runtime requires what microservices, and each of which does what*.

### Build your first GNES app

Let's start with a typical indexing procedure by writing a YAML config (see the left column of the table):

<table>
<tr>
<th>YAML config</th><th>GNES workflow (generated by <a href="https://board.gnes.ai">GNES board</a>)</th>
</tr>
<tr>
<td width="30%">
   <pre lang="yaml">
port: 5566
services:
- name: Preprocessor
 yaml_path: text-prep.yaml
- name: Encoder
 yaml_path: gpt2.yml
- name: Indexer
 yaml_path: b-indexer.yml
   </pre>
</td>
<td width="70%">
  <img src=".github/mermaid-diagram-20190723165430.svg" alt="GNES workflow of example 1">
</td>
</tr>
</table>

The YAML config should be pretty intuitive. It defines a pipeline workflow consists of preprocessing, encoding and indexing, where the output of the former component is the input of the next. For each component, we also associate it with a YAML config specifying how it should work. Right now they are not important for understanding the big picture, nonetheless curious readers can checkout how each YAML looks like by expanding the text below.

<details>
 <summary>Encoder config: gpt2.yml (click to expand...)</summary>
 
```yaml
!PipelineEncoder
component:
  - !GPT2Encoder
    parameter:
      model_dir: $GPT2_CI_MODEL
      pooling_stragy: REDUCE_MEAN
    gnes_config:
      is_trained: true
  - !PCALocalEncoder
    parameter:
      output_dim: 32
      num_locals: 8
    gnes_config:
      batch_size: 2048
  - !PQEncoder
    parameter:
      cluster_per_byte: 8
      num_bytes: 8
```

</details>

As a cloud-native application, GNES requires an **orchestration engine** to coordinate all micro-services. Currently, we support Kubernetes, Docker Swarm and a built-in solution.  Click on one of the icons below to get started.

<p align="center">
<table>
  <tr>
    <th>
    <img src=".github/orch-kubernetes.png?raw=true" alt="GNES on Kubernetes" height="64px" width="64px">
    <br>
    <a href="#using-gnes-with-kubernetes"> ▶️ I want to use GNES with Kubernetes.</a>
    </th>
    <th>
    <img src=".github/orch-dockerswarm.png?raw=true" alt="GNES on Docker Swarm" height="64px" width="64px">
    <br>
    <a href="#using-gnes-with-docker-swarm"> ▶️ I want to use GNES with Docker Swarm.</a>
    </th>
    <th>
    <img src=".github/orch-cli.png?raw=true" alt="GNES with built-in orchestration" height="64px" width="64px">
    <br>
    <a href="#using-gnes-with-built-in-orchestration"> ▶️ I want to use GNES on a single machine.</a>
    </th>
  </tr>
</table>
</p>



### Using GNES with Kubernetes

TBA

### Using GNES with Docker Swarm

The easiest and the recommended way to use GNES is via Docker, which uses containers to create virtual environments that isolate a GNES installation from the rest of the system. You don't need to worry about dependencies, they are self-contained in the GNES docker image. Moreover, GNES relies on the Docker Swarm for managing, scaling and conducting orchestration tasks over multiple micro-services. 

#### 1. Prerequisites

- [Docker Engine>=1.13](https://docs.docker.com/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Docker Machine](https://docs.docker.com/machine/install-machine/)


#### 2. Start GNES with the wizard

If you are new to GNES, it is recommended to use the wizard to config and start GNES.

```bash
bash <(curl -s https://raw.githubusercontent.com/gnes-ai/wizard/build/wizard.sh)
```

At the last step, the wizard will generate a random name for the service, say `my-gnes-0531`. Keep that name in mind. If you miss that name, you can always use `docker stack ls` to checkout the name of your service.

<details>
 <summary>How do I know if GNES is running succesfully? (click to expand...)</summary>

To tell whether the service is running successfully or not, you can use `docker stack ps my-gnes-0531`. It should give you results as follows:
```bash
ID                  NAME                         IMAGE                                           NODE                DESIRED STATE       CURRENT STATE                ERROR               PORTS
zku2zm9deli9        my-gnes-0531_encoder.1      ccr.ccs.tencentyun.com/gnes/aipd-gnes:86c0a3a   VM-0-3-ubuntu       Running             Running about an hour ago
yc09pst6s7yt        my-gnes-0531_grpc_serve.1   ccr.ccs.tencentyun.com/gnes/aipd-gnes:86c0a3a   VM-0-3-ubuntu       Running             Running about an hour ago
```

Note, the running status under `CURRENT STATE` suggests everything is fine.

</details>

<details>
<summary>How can I terminate GNES? (click to expand...)</summary>

To stop a running GNES service, you can use `docker stack rm my-gnes-0531`.

- Having troubles to start GNES? Checkout our [troubleshooting guide](#).
- For pro-users/developers, you may want to use our `gnes-yaml.sh` tools to [generate a YAML config via CLI](#); or simply [handcraft your own `docker-compose.yml`](#).

</details>



### Using GNES with Built-In Orchestration

TBA

<h2 align="center">Usage</h2>

First thing to know, GNES has **three independent runtimes**: train, index and search. This differs from the classic machine learning system which has two runtimes i.e. train and inference; also differs from the classic search system that has two runtimes i.e. index and search. Depending on the runtime of GNES, the microservices may be composed, work and communicate with others in different ways. In other word, the runtime determines which service doing what logic at when. In the sequel, we will demonstrate how to use GNES under different runtimes. 

Note, to switch between runtimee you need to shutdown the current runtime and start a new GNES.

### Train mode: training encoders and indexers

TBA

### Index mode: adding new documents

TBA

### Query mode: searching relevant documents of a given query

TBA  


<h2 align="center">Documentation</h2>

[![ReadTheDoc](https://readthedocs.org/projects/gnes/badge/?version=latest&style=for-the-badge)](https://doc.gnes.ai)

The official documentation of GNES is hosted on [doc.gnes.ai](https://doc.gnes.ai/). It is automatically built, updated and archived on every new release.

<h2 align="center">Tutorial</h2>

TBA

<h2 align="center">Contributing</h2>

Thanks for your interest in contributing! 

- [Contributor guidelines](./CONTRIBUTING.md)
- [Open issues](/issues)
- [Release notes](./CHANGELOG.md)

For contributors looking to get deeper into the API we suggest cloning the repository and checking out the unit tests for examples of how to call methods.




<h2 align="center">Citing GNES</h2>

```latex
@misc{tencent2019GNES,
  title={GNES: Generic Neural Elastic Search},
  author={Xiao, Han and Yan, Jianfeng and Wang, Feng and Fu, Jie},
  howpublished={\url{https://github.com/gnes-ai}},
  year={2019}
}
```

<h2 align="center">License</h2>

Tencent is pleased to support the open source community by making GNES
available.

Copyright (C) 2019 THL A29 Limited, a Tencent company. All rights reserved.

If you have downloaded a copy of the GNES binary or source code, please note that the GNES binary and source code are both licensed under the [Apache License, Version 2.0](./LICENSE).