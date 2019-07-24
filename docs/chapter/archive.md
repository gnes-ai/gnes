

Click on one of the icons below to get started.

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