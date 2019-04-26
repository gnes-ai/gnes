version: '3.4'
services:
  income-proxy:
    image: ${DOCKER_IMG_URL}
    command: >
      proxy --proxy_type MapProxyService --port_in ${INCOME_PROXY_IN} --port_out ${INCOME_PROXY_OUT}
      --socket_in PULL_BIND --socket_out PUSH_BIND --batch_size=${BATCH_SIZE}
    networks:
      gnes-net:
        aliases:
          - income_proxy
    ports:
      - ${HOST_PORT_IN}:${INCOME_PROXY_IN}
    deploy:
      placement:
        constraints: [node.role == worker]
      replicas: 1
      restart_policy:
        condition: on-failure
        max_attempts: 3

  middleman-proxy:
    image: ${DOCKER_IMG_URL}
    command: >
      proxy --proxy_type=ProxyService --port_in ${MIDDLEMAN_PROXY_IN} --port_out ${MIDDLEMAN_PROXY_OUT}
      --socket_in PULL_BIND --socket_out PUSH_BIND
      --unk_msg_route DEFAULT
    networks:
      gnes-net:
        aliases:
          - middleman_proxy
    deploy:
      placement:
        constraints: [node.role == worker]

  outgoing-proxy:
    image: ${DOCKER_IMG_URL}
    command: >
      proxy --proxy_type=ProxyService --port_in ${OUTGOING_PROXY_IN} --port_out ${OUTGOING_PROXY_OUT}
      --socket_in PULL_BIND --socket_out PUB_BIND
      --unk_msg_route DEFAULT
    networks:
      gnes-net:
        aliases:
          - outgoing_proxy
    ports:
      - ${HOST_PORT_OUT}:${OUTGOING_PROXY_OUT}
    deploy:
      placement:
        constraints: [node.role == worker]

  encoder:
    image: ${DOCKER_IMG_URL}
    command: >
      encode --port_in ${INCOME_PROXY_OUT} --port_out ${MIDDLEMAN_PROXY_IN}
      --socket_in PULL_CONNECT --socket_out PUSH_CONNECT
      --host_in income-proxy --host_out middleman-proxy
      --mode ADD --yaml_path /test_encoder.yml --dump_path /dump/model.bin
    volumes:
      - "${YAML_PATH}/encoder.yml.${ENC_NAME}:/test_encoder.yml"
      - "${MODEL_DIR}:/ext_data"
      - "${ENC_DIR}/${ENC_NAME}:/dump"
    networks:
      gnes-net:
        aliases:
          - encoder_serviced
    deploy:
      placement:
        constraints: [node.role == worker]
      replicas: 1
      restart_policy:
        condition: on-failure
        max_attempts: 3

    depends_on:
      - income-proxy
      - middleman-proxy

  indexer:
    image: ${DOCKER_IMG_URL}
    command: >
      index --port_in ${MIDDLEMAN_PROXY_OUT} --port_out ${OUTGOING_PROXY_IN}
       --socket_in PULL_CONNECT --socket_out PUSH_CONNECT
       --host_in middleman-proxy --host_out outgoing-proxy
       --mode ADD --yaml_path /indexer.yml --dump_path /out_data/test_index.bin
    volumes:
      - "${YAML_PATH}/indexer.yml:/indexer.yml"
      - index_data:/out_data
      #- type: volume
      #  source: "index_data"
      #  target: "/out_data"

      #- "${OUTPUT_DIR}/indexer_dump.{{.Task.Slot}}:/out_data"

    deploy:
      placement:
        constraints: [node.role == worker]
      replicas: 3
      restart_policy:
        condition: on-failure
        max_attempts: 3

    environment:
      - NODE_ID={{.Node.ID}}
      - SERVICE_ID={{.Service.ID}}
      - SERVICE_NAME={{.Service.Name}}
      - SERVICE_LABELS={{.Service.Labels}}
      - TASK_ID={{.Task.ID}}
      - TASK_NAME={{.Task.Name}}
      - TASK_SLOT={{.Task.Slot}}

    networks:
      gnes-net:
        aliases:
          - index_serviced
    depends_on:
      - middleman-proxy
      - outgoing-proxy

volumes:
  index_data:
    driver: vieux/sshfs:latest
    driver_opts:
      sshcmd: "ubuntu@172.17.0.8:/data/larry/save_data/shard_{{ .Task.Slot }}_data"
      password: "!QAZ2wsx#EDC"
      allow_other: ""
    name: 'shard_{{ .Task.Slot }}_data'
    #external:
    #  name: 'index_shard_{{ .Task.Slot }}_data'

networks:
  gnes-net:
    driver: overlay
    attachable: true
