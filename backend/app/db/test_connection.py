from app.db.database import SessionLocal
from app.models.repository import Repository


def main() -> None:
    db = SessionLocal()

    try:
        repository = Repository(
            name="RepoGuard Demo",
            source_type="github",
            source_url="https://github.com/example/repoguard-demo",
            default_branch="main",
        )

        db.add(repository)
        db.commit()
        db.refresh(repository)

        print("Repository created successfully!")
        print(f"ID: {repository.id}")
        print(f"Name: {repository.name}")
        print(f"Source: {repository.source_type}")
        print(f"URL: {repository.source_url}")

    finally:
        db.close()


if __name__ == "__main__":
    main()