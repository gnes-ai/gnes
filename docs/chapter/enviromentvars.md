# Environment Variables 

There are couple of environment variables that GNES respect during runtime.

## `GNES_PROFILING`

Set to any non-empty string to turn on service-level time profiling for GNES.

Default is disabled.

## `GNES_PROFILING_MEM`

Set to any non-empty string to turn on service-level memory profiling for GNES. Warning, memory profiling could hurt the efficiency significantly.

Default is disabled.

## `GNES_WARN_UNNAMED_COMPONENT`

Set to `0` to turn off the warning like `this object is not named ("name" is not found under "gnes_config" in YAML config), i will call it "BaseRouter-51ce94cc". naming the object is important as it provides an unique identifier when serializing/deserializing this object.`

Set to `1` to enable it. 

Default is enabled.

## `GNES_VCS_VERSION`

Git version of GNES. This is used when `--check_version` is turned on. For GNES official docker image, `GNES_VCS_VERSION` is automatically set to the git version during the building procedure.

Default is the git head version when building docker image. Otherwise it is not set.

## `GNES_CONTROL_PORT`

Control port of the microservice. Useful when doing health check via `gnes healthcheck`.

Default is not set. A random port will be used.

## `GNES_CONTRIB_MODULE`

(*depreciated*) Paths of the third party components. See examples in GNES hub for latest usage.

## `GNES_IPC_SOCK_TMP`

Temp directory for ipc sockets, not used on Windows.