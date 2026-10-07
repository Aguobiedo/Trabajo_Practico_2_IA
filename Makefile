.PHONY: help up down restart logs status build

help:
	@echo "Targets: up, down, restart, logs, status, build"

up:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

status:
	docker compose ps

build:
	docker compose build
