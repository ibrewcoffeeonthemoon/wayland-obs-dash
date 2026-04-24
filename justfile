# lint
check-format:
    ruff check --fix .

# type check
check-types:
    mypy .

# all
check-all: check-format check-types

