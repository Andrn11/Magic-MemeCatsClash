from pathlib import Path


def create_quests_structure():
    """Создает структуру папок для квестов"""
    base_dir = Path("quests_data")
    dirs = [
        base_dir / "user_progress_json_files",
        base_dir / "available_quests",
        base_dir / "available_quests/available_quests_cat",
        base_dir / "available_quests/available_quests_magic",
        base_dir / "available_quests/available_quests_melodygame"
    ]

    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Создана папка: {directory}")


if __name__ == "__main__":
    create_quests_structure()