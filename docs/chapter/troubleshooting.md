# Troubleshooting


## Check if docker swarm/stack runs successfully

```bash
docker service ls
```

```text
ID                  NAME                              MODE                REPLICAS            IMAGE                                           PORTS
j7b533zxmzg5        gnes-swarm-2654_encoder           replicated          0/1                 ccr.ccs.tencentyun.com/gnes/aipd-gnes:master
0vlxu4acg1ph        gnes-swarm-2654_income-proxy      replicated          0/1                 ccr.ccs.tencentyun.com/gnes/aipd-gnes:master    *:4962->4962/tcp
equqrhsn7pky        gnes-swarm-2654_indexer           replicated          0/3                 ccr.ccs.tencentyun.com/gnes/aipd-gnes:master
nd7euo7mcpa9        gnes-swarm-2654_middleman-proxy   replicated          0/1                 ccr.ccs.tencentyun.com/gnes/aipd-gnes:master
ssdlk9gzmggw        gnes-swarm-2654_outgoing-proxy    replicated          0/1                 ccr.ccs.tencentyun.com/gnes/aipd-gnes:master    *:4963->4963/tcp
xgxeetyhos6t        my-gnes_encoder                   replicated          1/1                 ccr.ccs.tencentyun.com/gnes/aipd-gnes:a799a0f
zny37400p225        my-gnes_income-proxy              replicated          1/1                 ccr.ccs.tencentyun.com/gnes/aipd-gnes:a799a0f   *:8598->8598/tcp
taqqg6qwrxlw        my-gnes_indexer                   replicated          3/3                 ccr.ccs.tencentyun.com/gnes/aipd-gnes:a799a0f
j96gnny8ysbn        my-gnes_middleman-proxy           replicated          1/1                 ccr.ccs.tencentyun.com/gnes/aipd-gnes:a799a0f
e28spnuksjw8        my-gnes_outgoing-proxy            replicated          1/1                 ccr.ccs.tencentyun.com/gnes/aipd-gnes:a799a0f   *:8599->8599/tcp
```

In the above example, we started two swarms, i.e. `gnes-swarm-2654` and `my-gnes`. Unfortunately, `gnes-swarm-2654` fails to start and is not running at all. But how can one tell that?

Note the column `REPLICAS`, which indicates the number of running service (versus the number of required services). `gnes-swarm-2654` gives `0/0` for all services. This suggests the swarm fails to start. The next step is to investigate the reason.

## Investigate the reason of a failed service 

One can not print out all logs of a docker swarm. Instead, one can inspect service by service, e.g.

```bash
docker service ps gnes-swarm-2654_encoder --format "{{json .Error}}" --no-trunc
```

```text
"\"invalid mount config for type \"bind\": bind source path does not exist: /data/han/test-shell/output_data\""
"\"invalid mount config for type \"bind\": bind source path does not exist: /data/han/test-shell/output_data\""
"\"invalid mount config for type \"bind\": bind source path does not exist: /data/han/test-shell/output_data\""
"\"invalid mount config for type \"bind\": bind source path does not exist: /data/han/test-shell/output_data\""
```

Now the reason is clear, `output_data` does not exist when starting the swarm. But why there are duplicated lines there? This is because docker swarm did three retries before giving up on starting this service, where each time it met the same problem. Thus four duplicated lines in total.

## Delete a failed service

Now that the reason is clear, we can delete the failed service and release the resources.

```bash
docker stack rm gnes-swarm-2654
```

```text
Removing service gnes-swarm-2654_encoder
Removing service gnes-swarm-2654_income-proxy
Removing service gnes-swarm-2654_indexer
Removing service gnes-swarm-2654_middleman-proxy
Removing service gnes-swarm-2654_outgoing-proxy
Removing network gnes-swarm-2654_gnes-net
```

## Locate internal errors by looking at logs

Sometime the service fails to start but `docker service ps` gives no error, 

```bash
docker service ps gnes-swarm-4254_encoder --format "{{json .Error}}" --no-trunc
```

```text
""
```

Or it shows an error that is not explanatory.

```bash
"\"task: non-zero exit (2)\""
```

Often in this case, the service fails to start *not* due tothe docker config, but due to the GNES internal error. To see that, 

```bash
docker service logs gnes-swarm-4254_income-proxy
``` 

```bash
gnes-swarm-4254_income-proxy.1.yj5v8n4dhfgv@VM-0-3-ubuntu    |                   [--proxy_type {BS,Dict,MapProxyService,Message,MessageHandler,ProxyService,ReduceProxyService,defaultdict}]
gnes-swarm-4254_income-proxy.1.yj5v8n4dhfgv@VM-0-3-ubuntu    |                   [--batch_size BATCH_SIZE] [--num_part NUM_PART]
gnes-swarm-4254_income-proxy.1.kmgk21qo6m0n@VM-0-3-ubuntu    |                   [--proxy_type {BS,Dict,MapProxyService,Message,MessageHandler,ProxyService,ReduceProxyService,defaultdict}]
gnes-swarm-4254_income-proxy.1.w04d552cuj93@VM-0-3-ubuntu    | gnes proxy: error: argument --batch_size: invalid int value: ''
gnes-swarm-4254_income-proxy.1.kmgk21qo6m0n@VM-0-3-ubuntu    |                   [--batch_size BATCH_SIZE] [--num_part NUM_PART]
```

One can now clearly see that the error comes from an incorrectly given `--batch_size`, which throws from GNES CLI. 