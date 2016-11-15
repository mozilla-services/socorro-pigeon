DC := $(shell which docker-compose)

default:
	@echo "You need to specify a subcommand."
	@exit 1

help:
	@echo "build         - build docker containers for dev"
	@echo "shell         - open a shell in the base container"
	@echo "test          - run tests"

# Dev configuration steps
.docker-build:
	make build

build:
	${DC} build lambda
	touch .docker-build

shell: .docker-build
	${DC} run lambda bash

test: .docker-build
	${DC} run lambda py.test

.PHONY: default build shell test
