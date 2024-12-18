import os
import zlib
from hashlib import sha1
import sys
from datetime import datetime
import subprocess


def read_git_object(repo_path, object_hash):
    """Читает и распаковывает Git-объект из директории .git/objects."""
    object_dir = os.path.join(repo_path, ".git", "objects", object_hash[:2])
    object_file_path = os.path.join(object_dir, object_hash[2:])
    
    if not os.path.exists(object_file_path):
        raise FileNotFoundError(f"Git объект {object_hash} не найден в {object_file_path}")
    
    with open(object_file_path, 'rb') as file:
        compressed_data = file.read()
    
    return zlib.decompress(compressed_data)


def parse_commit_object(commit_data):
    """Разбирает объект commit и извлекает метаданные, включая родительские коммиты."""
    lines = commit_data.split('\n')
    parents = []
    tree_hash = None
    author_time = None
    
    for line in lines:
        if line.startswith("tree"):
            tree_hash = line.split()[1]
        elif line.startswith("parent"):
            parents.append(line.split()[1])
        elif line.startswith("author"):
            # Извлечение временной метки из строки с автором
            author_time = int(line.split()[-2])
        elif line == '':
            break
    
    return tree_hash, parents, author_time


def get_all_commits(repo_path, date_before):
    """Получает все хэши и временные метки коммитов из репозитория, сканируя .git/objects,
    включая только коммиты до указанной даты."""
    objects_dir = os.path.join(repo_path, ".git", "objects")
    commits = []
    
    for root, dirs, files in os.walk(objects_dir):
        for filename in files:
            object_hash = os.path.basename(root) + filename
            try:
                object_data = read_git_object(repo_path, object_hash)
                if object_data.startswith(b'commit'):
                    _, parents, author_time = parse_commit_object(object_data.decode('utf-8'))
                    if author_time <= date_before:
                        commits.append((object_hash, author_time))
            except Exception:
                continue
    
    # Сортировка коммитов по временной метке (от ранних к поздним)
    commits.sort(key=lambda x: x[1])
    return [commit_hash for commit_hash, _ in commits]


def build_commit_graph(repo_path, date_before):
    """Создает граф зависимостей коммитов, анализируя все объекты commit."""
    commit_graph = {}
    commit_hashes = get_all_commits(repo_path, date_before)
    
    for commit_hash in commit_hashes:
        commit_data = read_git_object(repo_path, commit_hash).decode('utf-8')
        _, parents, _ = parse_commit_object(commit_data)
        commit_graph[commit_hash] = parents
    
    return commit_graph


def generate_plantuml(commit_graph):
    """Генерирует текст PlantUML для графа зависимостей коммитов, обеспечивая зависимости от ранних к поздним коммитам."""
    plantuml_lines = ["@startuml"]

    # Обеспечение зависимостей от ранних к поздним коммитам путем итерации по порядку
    i = 1
    for commit, parents in commit_graph.items():
        if parents:
            for parent in parents:
                plantuml_lines.append(f"\"{parent} ({i})\" --> \"{commit} ({i+1})\"")
                i+=1
    
    plantuml_lines.append("@enduml")
    return "\n".join(plantuml_lines)


def save_plantuml_file(plantuml_text, plantuml_file_path):
    """Сохраняет текст PlantUML в файл."""
    with open(plantuml_file_path, 'w') as file:
        file.write(plantuml_text)


def generate_graph_image(plantuml_file_path, output_image_path, plantuml_jar_path):
    """Создает изображение из файла PlantUML с использованием JAR PlantUML."""
    plantuml_cmd = ['java', '-jar', plantuml_jar_path, plantuml_file_path, '-tpng', '-o', os.path.dirname(output_image_path)]
    result = subprocess.run(plantuml_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Ошибка при запуске PlantUML: {result.stderr}")
    
    generated_image_path = plantuml_file_path.replace(".puml", ".png")
    os.rename(generated_image_path, output_image_path)


def main(repo_path, date_before, output_image_path, plantuml_jar_path):
    # Преобразование строки date_before в метку времени UNIX
    date_before_timestamp = int(datetime.strptime(date_before, "%Y-%m-%d").timestamp())
    
    # 1. Создание графа коммитов вручную из Git объектов
    commit_graph = build_commit_graph(repo_path, date_before_timestamp)
    
    # 2. Генерация текста PlantUML для графа коммитов
    plantuml_text = generate_plantuml(commit_graph)
    
    # 3. Сохранение текста PlantUML в файл
    plantuml_file_path = output_image_path.replace('.png', '.puml')
    save_plantuml_file(plantuml_text, plantuml_file_path)
    
    # 4. Создание изображения из файла PlantUML
    generate_graph_image(plantuml_file_path, output_image_path, plantuml_jar_path)
    
    print(f"Граф коммитов успешно сохранен в {output_image_path}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Использование: python main.py <repo_path> <date_before> <output_image_path> <plantuml_jar_path>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    date_before = sys.argv[2]
    output_image_path = sys.argv[3]
    plantuml_jar_path = sys.argv[4]

    try:
        main(repo_path, date_before, output_image_path, plantuml_jar_path)
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)