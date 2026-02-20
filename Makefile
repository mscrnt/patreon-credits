.PHONY: dev prod down build lint clean logs health

# Development — hot reload on http://localhost:5000
dev:
	docker compose --profile dev up --build

# Production — headless on http://localhost:8787
prod:
	docker compose --profile prod up -d --build

# Stop all containers
down:
	docker compose --profile dev --profile prod down

# Build images without starting
build:
	docker compose --profile dev --profile prod build

# Run linter
lint:
	ruff check .

# Remove generated videos and __pycache__
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	rm -f output/*.mp4 static/output/*.mp4

# Tail container logs (prod)
logs:
	docker compose --profile prod logs -f

# Health check (prod)
health:
	@curl -sf http://localhost:8787/health && echo || echo "Not running"
