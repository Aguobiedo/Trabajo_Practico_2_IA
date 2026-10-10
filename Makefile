.PHONY: help up down restart logs status build redis

help:
	@echo "Targets: up, down, restart, logs, status, build, redis"

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

redis:
	docker compose up -d redis
