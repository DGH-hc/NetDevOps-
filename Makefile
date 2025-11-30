.PHONY: build run worker migrate lint format test up down logs

# Build Docker image
build:
	docker build -t netdevops:dev .

# Run the API container locally (dev mode — mapped to port 8000)
run:
	docker run -p 8000:8000 netdevops:dev

# Run Celery worker inside container
worker:
	docker run netdevops:dev \
		celery -A app.worker.celery_app.app worker --loglevel=info

# Apply Alembic migrations
migrate:
	alembic upgrade head

# Generate new Alembic migration
revision:
	alembic revision --autogenerate -m "auto update"

# Lint code using Ruff
lint:
	ruff check app

# Fix code style automatically
format:
	ruff check app --fix

# Run pytest
test:
	pytest -q

# Bring up full docker-compose stack
up:
	docker compose up --build

# Stop stack
down:
	docker compose down

# Tail logs from API container
logs:
	docker compose logs -f app
