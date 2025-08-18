@run:
    uv run granian --interface asgi --host 0.0.0.0 --port 8000 --reload main:app

@up:
    docker compose up

@down:
    docker compose down

@test:
    uv run pytest
