#!/bin/bash
# Makefile for Bookshop project
DOCKER := docker
DOCKER_COMPOSE := docker-compose
PROJECT_CONTAINER := bookshop
PYTHON := python
PYTEST := pytest
TEST_FILE := api_test.py

.PHONY: all db_env test run clean

all: run test

db_env:
	# Prepare DB volume
	if [ ! $(ls -d $(HOME)/data/postgresql) ]; then \
		mkdir -p $(HOME)/data/postgresql; \
	fi

run: clean db_env
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml up -d

test:
	$(DOCKER) exec -it $(PROJECT_CONTAINER) sh -c "$(PYTHON) -m $(PYTEST) tests/$(TEST_FILE)" 

# Target: Clean up compiled files and caches
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	$(DOCKER_COMPOSE) down
