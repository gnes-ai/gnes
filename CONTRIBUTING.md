# Contributing to GNES

🙇 Thanks for your interest in contributing! GNES always welcome the contribution from the open-source community, individual committers and other partners. Without you, GNES can't be successful.

## ❤️ Making Your First Commit 

The beginning is always the hardest. But fear not, even if you find a typo, a missing docstring or unit test, you can simply correct them by making a commit to GNES. Here are the steps:

1. Create a new branch, say `fix-gnes-typo-1`
2. Fix/improve the codebase
3. Commit the changes. Note the **commit message must follow [the naming style](#commit-message-naming)**, say `fix(readme): improve the readability and move sections`
4. Make a pull request. Note the **commit message must follow [the naming style](#commit-message-naming)**. It can simply be one of your commit messages, just copy paste it, e.g. `fix(readme): improve the readability and move sections`
5. Submit your pull request and wait for all checks passed (usually 10 minutes)
    - Coding style
    - Commit and PR styles check
    - All unit tests
6. Request reviews from one of the developers from our core team.
7. Get a LGTM 👍 and PR gets merged.

Well done! Once a PR gets merged, here are the things happened next:
- all Docker images tagged with `-latest` will be automatically updated in an hour. You may check the [its building status at here](https://github.com/gnes-ai/gnes/#install-gnes-via-pip)
- on every Friday when a new release is published, PyPi packages and all Docker images tagged with `-stable` will be updated accordindly. 
- your contribution and commits will be included in [our weekly release note](https://github.com/gnes-ai/gnes/blob/master/CHANGELOG.md). 🍻


## Table of Content

* [Commit Message Naming](#commit-message-naming)
* [Merging Process](#merging-process)
* [Release Process](#release-process)
  - [Major and minor version increments](#major-and-minor-version-increments)
* [Testing Locally](#testing-locally)
* [Interesting Points](#intersting-points)
  
## Commit Message Naming

To help everyone with understanding the commit history of GNES, we employ [`commitlint`](https://commitlint.js.org/#/) in the CI pipeline to enforce the commit styles. Specifically, our convention is:

```text
type(scope?): subject
```

where `type` is one of the following:

- build
- ci
- chore
- docs
- feat
- fix
- perf
- refactor
- revert
- style
- test

`scope` is optional, represents the module your commit working on.

`subject` explains the commit.

As an example, a commit that implements a new encoder should be phrased as:
```text
feat(encoder): add new inceptionV3 as image encoder
``` 

## Merging Process

A pull request has to meet the following conditions to be merged into master:

- Coding style check (PEP8, via Codacy)
- Commit style check (in CI pipeline via Drone.io)
- Unit tests (via Drone.io)
- Review and approval from a GNES team member.

After the merging is triggered, the build will be delivered to the followings:

- **Docker Hub**: `gnes:latest` will be updated.
- **Tencent Container Service**: `gnes:latest` will be updated.
- **ReadTheDoc**: `latest` will be updated.
- **Benchmark**: [speed test](https://github.com/gnes-ai/benchmark) will be updated.

Note that merging into master does not mean an official releasing. For the releasing process, please refer to the next section.

## Release Process

A new release is scheduled on every Friday (triggered and approved by [Han Xiao](https://github.com/hanxiao)) summarizing all new commits since the last release. The release will increment the third (revision) part of the version number, i.e. from `0.0.24` to `0.0.25`.

After a release is triggered, the build will be delivered to the followings:

- **Docker Hub**: a new image with the release version tag will be created, `gnes:latest` will be updated.
- **Tencent Container Service**: a new image with the release version tag will be created, `gnes:latest` will be updated.
- **PyPi Package**: a new version of Python package is uploaded to Pypi, allowing one to `pip install -U gnes` 
- **ReadTheDoc**: a new version of the document will be built, `latest` will be updated and the old version will be achieved
- **Benchmark**: [speed test](https://github.com/gnes-ai/benchmark) will be updated.

Meanwhile, a new pull request containing the updated [CHANGELOG](./CHANGELOG.md) and the new version number will be made automatically, pending for review and merge.

#### Major and minor version increments

- MAJOR version when GNES make incompatible API changes;
- MINOR version when GNES add functionality in a backwards-compatible manner.

The decision of incrementing major and minor version, i.e. from `0.0.0` to `0.1.0` or from `1.0.0` to `2.0.0`, is made by the GNES team.

## Testing Locally

The best way to test GNES is using a Docker container, in which you don't have to worry about the dependencies.

We provide a public Docker image `gnes/ci-base`, which contains the required dependencies and some pretrained models used in our continuous integration pipeline.

You can [find the image at here](https://cloud.docker.com/u/gnes/repository/docker/gnes/ci-base) or pull the image via:
```bash
docker pull gnes/ci-base
```

To test GNES inside this image, you may run

```bash
docker run --network=host --rm --entrypoint "/bin/bash" -it gnes/ci-base

# now you are inside the 'gnes/ci-base' container
# first sync your local modification, then
pip install -e .[all]
python -m unittest tests/*.py
``` 

## Interesting Points 

Currently there are three major directions of contribution:
- **Porting state-of-the-art models to GNES**. This includes new preprocessing algorithms, new DNN networks for encoding, and new high-performance index. Believe me, it is super easy to wrap an algorithm and use it in GNES. Checkout this example.
- **Adding tutorial and learning experience**. What is good and what can be improved? If you apply GNES in your domain, whether it's about NLP or CV, whether it's a blog post or a Reddit/Twitter thread, we are always eager to hear your thoughts.
- **Completing the user experience of other programming languages**. GNES offers a generic interface with gRPC and protobuf, therefore it is easy to add an interface for other languages, e.g. Java, C, Go. 
