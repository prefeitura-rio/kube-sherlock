default_compose_file := "docker-compose.yaml"
debug_compose_file := "docker-compose.debug.yaml"
compose_file := if env("DEBUG", "false") == "true" { debug_compose_file } else { default_compose_file }

@watch:
    docker compose -f {{ compose_file }} up --watch --build

@up:
    docker compose -f {{ compose_file }} up --build

@down:
    docker compose -f {{ compose_file }} down --remove-orphans

@test:
    uv run pytest

@typecheck:
    uv run mypy src/
