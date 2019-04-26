.SHELL=/bin/bash
.DEFAULT_GOAL:=help

include env
export $(shell sed 's/=.*//' env)

define random_port
$(shell shuf -i 2000-65000 -n 1)
endef

export INCOME_PROXY_OUT=$(call random_port)
export MIDDLEMAN_PROXY_IN=$(call random_port)
export MIDDLEMAN_PROXY_OUT=$(call random_port)
export OUTGOING_PROXY_IN=$(call random_port)

train: ##build yaml for train service
	@envsubst < yaml/train-compose.yml > train-compose.yml
	$(info use the following command to start train service:)
	$(info docker stack deploy --compose-file ./train-compose.yml gnes-train)

add: ##build yaml for add service 
	@envsubst < yaml/add-compose.yml > add-compose.yml
	$(info use the following command to start add service:)
	$(info docker stack deploy --compose-file ./add-compose.yml gnes-add)

query: ##build yaml for query service
	@envsubst < yaml/query-compose.yml > query-compose.yml
	$(info use the following command to start query service:)
	$(info docker stack deploy --compose-file ./query-compose.yml gnes-query)
all: train add query ## build all service yamls

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)