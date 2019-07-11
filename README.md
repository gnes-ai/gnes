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
  <a href="#install">Install</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#usage">Usage</a> •
  <a href="#book-tutorial">Tutorials</a> •
  <a href="#speech_balloon-faq">FAQ</a>  
</p>

<h2 align="center">What is it</h2>

GNES [<i>jee-nes</i>] is Generic Neural Elastic Search, a cloud-native semantic search system based on deep neural network. 


GNES enables large-scale index and semantic search for text-to-text, image-to-image, video-to-video and possibly any-to-any content form.


<h2 align="center">Highlights</h2>

- :cloud: **Cloud-native**: GNES is *all-in-microservice*: encoder, indexer, preprocessor and router are all running statelessly and independently in their own containers.  They communicate via versioned APIs and collaborate under the orchestration of Docker Swarm/Kubernetes etc. Scaling, load-balancing, automated recovering, they come off-the-shelf in GNES.
- :hatching_chick: **Easy-to-use on every level**: How long would it take to deploy a change that involves just changing the encoder from BERT to ELMO or switching a layer in VGG? In GNES, this is just one line change in a YAML file. We abstract the encoding and indexing logic from the code to a YAML config, so that you can combine or stack encoders and indexers without even touching the codebase.
- :rocket: **State-of-the-art**: Taking advantage of fast-evolving AI/ML/NLP/CV communities, we learn from best-of-breed deep learning models and plug them into GNES, making sure you always enjoy the state-of-the-art performance.
- :nut_and_bolt: **Generic and compatible**: Searching for texts, image or even short-videos? Using Python/C/Java/Go/HTTP as the client? Doesn't matter which content form you have or which language do you use, GNES can handle them all. 
- :100: **Best practice**: We love to learn the best practice from the community, helping our GNES to achieve the next level of availability, resiliency, performance, and durability. If you have any ideas or suggestions, feel free to contribute.


<h2 align="center">Overview</h2>
<p align="center">
<img src=".github/gnes-component-overview.svg" alt="component overview">
</p>


<h2 align="center">Getting Started</h2>

As a cloud-native application, GNES requires an **orchestration engine** to coordinate all micro-services. Currently, we support Kubernetes, Docker Swarm and a built-in solution.  Click on one of the icons below to get started.

<p align="center">
<table>
  <tr>
    <th>
    <img src=".github/orch-kubernetes.png?raw=true" alt="GNES on Kubernetes" height="100px">
    <br>
    <a href="#using-gnes-with-kubernetes"> ▶️ I want to use GNES with Kubernetes.</a>
    </th>
    <th>
    <img src=".github/orch-dockerswarm.png?raw=true" alt="GNES on Docker Swarm" height="100px">
    <br>
    <a href="#using-gnes-with-docker-swarm"> ▶️ I want to use GNES with Docker Swarm.</a>
    </th>
    <th>
    <img src=".github/orch-cli.png?raw=true" alt="GNES with built-in orchestration" height="100px">
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


<h2 align="center">:book: Documentation</h2>

[![ReadTheDoc](https://readthedocs.org/projects/gnes/badge/?version=latest&style=for-the-badge)](https://doc.gnes.ai)

The official documentation of GNES is hosted on [doc.gnes.ai](https://doc.gnes.ai/). It is automatically built, updated and archived on every new release.


<h2 align="center">Tutorial</h2>

TBA

<h2 align="center">Contributing</h2>

Thanks for your interest in contributing! There are many ways to get involved; start with our [contributor guidelines](#) and then check these [open issues](/issues) for specific tasks.

For contributors looking to get deeper into the API we suggest cloning the repository and checking out the unit tests for examples of how to call methods.

<h2 align="center">Release Notes</h2>

TBA

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