import os
import json
from dependency_graph import load_config, get_git_commits, build_mermaid_graph, save_graph_as_png

def test_load_config():
    print("Testing load_config...")
    # Создаем временный конфигурационный файл
    config_path = "temp_config.json"
    config_data = {
        "repo_path": "/path/to/repo",
        "mermaid_cli_path": "/path/to/mmdc",
        "output_path": "/path/to/output.png",
        "since_date": "2024-01-01"
    }
    with open(config_path, "w") as f:
        json.dump(config_data, f)

    # Тестируем загрузку конфигурации
    loaded_config = load_config(config_path)
    assert loaded_config == config_data, f"Ошибка в load_config: {loaded_config}"
    print("load_config passed.")

    # Удаляем временный файл
    os.remove(config_path)

def test_get_git_commits():
    print("Testing get_git_commits...")
    # Настраиваем временный репозиторий
    repo_path = "temp_repo"
    if not os.path.exists(repo_path):
        os.makedirs(repo_path)

    os.chdir(repo_path)
    os.system("git init")
    os.system('git config user.name "Test User"')
    os.system('git config user.email "test@example.com"')

    # Создаем первый коммит
    with open("file.txt", "w") as f:
        f.write("Initial commit")
    os.system("git add file.txt")
    os.system("git commit -m 'Initial commit'")

    # Создаем второй коммит
    with open("file.txt", "a") as f:
        f.write("\nSecond commit")
    os.system("git add file.txt")
    os.system("git commit -m 'Second commit'")

    # Проверяем получение коммитов
    commits = get_git_commits(repo_path, "2023-01-01")
    assert len(commits) > 0, f"Ошибка в get_git_commits: коммиты не найдены. {commits}"
    print(f"get_git_commits passed. Найдено коммитов: {len(commits)}")

    # Чистим временные файлы
    os.chdir("..")
    os.system(f"rm -rf {repo_path}")

def test_build_mermaid_graph():
    print("Testing build_mermaid_graph...")
    commits = [
        ("abc123", ["def456"]),
        ("def456", ["ghi789"]),
        ("ghi789", [])
    ]
    expected_output = (
        "graph TD\n"
        "    abc123 --> def456\n"
        "    def456 --> ghi789\n"
    )
    mermaid_graph = build_mermaid_graph(commits)
    assert mermaid_graph.strip() == expected_output.strip(), f"Ошибка в build_mermaid_graph: {mermaid_graph}"
    print("build_mermaid_graph passed.")

def test_save_graph_as_png():
    print("Testing save_graph_as_png...")
    # Пример кода Mermaid
    mermaid_code = "graph TD\n    A --> B\n    B --> C\n"
    output_path = "temp_graph.png"
    mermaid_cli_path = "/path/to/mmdc"  # Укажите путь к mmdc

    # Пропускаем тест, если mmdc не доступен
    if not os.path.exists(mermaid_cli_path):
        print("Пропуск теста save_graph_as_png: mmdc не найден.")
        return

    save_graph_as_png(mermaid_code, output_path, mermaid_cli_path)
    assert os.path.exists(output_path), f"Ошибка в save_graph_as_png: файл {output_path} не создан."
    print("save_graph_as_png passed.")

    # Удаляем временный файл
    os.remove(output_path)

# Запуск тестов
if __name__ == "__main__":
    test_load_config()
    test_get_git_commits()
    test_build_mermaid_graph()
    test_save_graph_as_png()
    print("Все тесты пройдены.")
