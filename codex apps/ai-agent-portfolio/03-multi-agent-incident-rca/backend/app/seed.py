from .api import repository, seed_if_empty


def main() -> None:
    seed_if_empty()
    print(f"Seed complete: {len(repository.list_incidents())} deterministic incidents")


if __name__ == "__main__":
    main()

