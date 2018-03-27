DC := $(shell which docker-compose)
HOSTUSER := $(shell id -u):$(shell id -g)

default:
	@echo "You need to specify a subcommand. Type 'make help' for help."
	@exit 1

help:
	@echo "build        - install Python libs and build Docker containers"
	@echo "test         - run tests"
	@echo "testshell    - open a shell in the test container"
	@echo "clean        - remove build files"

.container-test: docker/test/Dockerfile requirements-dev.txt
	${DC} build test
	touch .container-test

build-containers: .container-test

build-libs:
	test -d build/ || mkdir build/
	# Install requirements and link pigeon into build/
	${DC} run -u "${HOSTUSER}" lambda-build pip install --disable-pip-version-check --ignore-installed --no-cache-dir -r /tmp/requirements.txt -t /tmp/build/
	cp pigeon.py build/pigeon.py

build: build-containers build-libs

clean:
	-rm -rf build
	-rm .container-*

test-flake8: .container-test
	${DC} run test flake8 pigeon.py

test-pytest: .container-test
	${DC} run test py.test

test: test-flake8 test-pytest

testshell: .container-test
	${DC} run test bash

.PHONY: default build clean build-containers build-libs build test-flake8 test-pytest test-integration test testshell
