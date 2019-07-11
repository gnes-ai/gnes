# Contributing to GNES

## Commit Message and Pull Request Naming

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