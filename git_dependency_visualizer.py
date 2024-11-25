#!/usr/bin/env python3
import os
import zlib
from datetime import datetime
import argparse

def parse_git_commit(commit_data):
    """Разбирает содержимое коммита."""
    lines = commit_data.splitlines()
    metadata, message = {}, []
    for line in lines:
        if line == "":
            break
        key, value = line.split(" ", 1)
        metadata[key] = value
    return metadata

def read_git_object(repo_path, object_hash):
    """Читает Git-объект из папки .git/objects."""
    obj_dir = os.path.join(repo_path, ".git", "objects", object_hash[:2])
    obj_file = os.path.join(obj_dir, object_hash[2:])
    with open(obj_file, "rb") as f:
        compressed_data = f.read()
    decompressed_data = zlib.decompress(compressed_data)
    header, data = decompressed_data.split(b"\x00", 1)
    return header.decode(), data.decode()

def list_git_commits(repo_path):
    """Возвращает список всех коммитов."""
    objects_dir = os.path.join(repo_path, ".git", "objects")
    commits = []
    for root, _, files in os.walk(objects_dir):
        for file in files:
            object_hash = os.path.basename(root) + file
            try:
                header, data = read_git_object(repo_path, object_hash)
                if header.startswith("commit"):
                    commits.append((object_hash, data))
            except Exception:
                continue
    return commits

def filter_commits_by_date(commits, since, until):
    """Фильтрует коммиты по диапазону дат."""
    filtered = []
    for object_hash, commit_data in commits:
        metadata = parse_git_commit(commit_data)
        commit_date = datetime.utcfromtimestamp(int(metadata["author"].split()[-2]))
        if since <= commit_date <= until:
            filtered.append((object_hash, commit_date))
    return sorted(filtered, key=lambda x: x[1], reverse=True)

def build_dependency_graph(repo_path, commits):
    """Строит граф зависимостей для коммитов."""
    graph = {}
    for object_hash, _ in commits:
        header, data = read_git_object(repo_path, object_hash)
        metadata = parse_git_commit(data)
        parent_hashes = metadata.get("parent", "").split()
        graph[object_hash] = parent_hashes
    return graph

def generate_graphviz(graph, commits):
    """Генерирует код Graphviz для графа."""
    dot = ["digraph G {"]
    dot.append("    node [shape=box, fontsize=10];")

    commit_dates = {commit[0]: commit[1] for commit in commits}
    for commit, parents in graph.items():
        label = f"{commit}\\n{commit_dates[commit].strftime('%Y-%m-%d %H:%M:%S')}"
        dot.append(f'    "{commit}" [label="{label}"];')
        for parent in parents:
            if parent in graph:
                dot.append(f'    "{commit}" -> "{parent}";')

    dot.append("}")
    return "\n".join(dot)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Генератор графа зависимостей коммитов.")
    parser.add_argument(
        "-r", "--repo-path",
        required=True,
        help="Путь к анализируемому Git-репозиторию."
    )
    parser.add_argument(
        "--since",
        required=True,
        help="Начальная дата диапазона в формате YYYY-MM-DD."
    )
    parser.add_argument(
        "--until",
        required=True,
        help="Конечная дата диапазона в формате YYYY-MM-DD."
    )
    parser.add_argument(
        "-o", "--output-file",
        required=True,
        help="Путь к файлу-результату в виде кода Graphviz."
    )
    return parser.parse_args()

def main():
    args = parse_arguments()

    repo_path = args.repo_path
    try:
        since = datetime.strptime(args.since, "%Y-%m-%d")
        until = datetime.strptime(args.until, "%Y-%m-%d")
    except ValueError:
        print("Ошибка: Даты должны быть в формате YYYY-MM-DD.")
        return

    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"Ошибка: Путь '{repo_path}' не является Git-репозиторием.")
        return

    commits = list_git_commits(repo_path)
    filtered_commits = filter_commits_by_date(commits, since, until)

    if not filtered_commits:
        print("Коммиты в указанном диапазоне не найдены.")
        return

    graph = build_dependency_graph(repo_path, filtered_commits)
    graphviz_code = generate_graphviz(graph, filtered_commits)

    try:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(graphviz_code)
        print(f"Graphviz код успешно записан в файл '{args.output_file}'.")
    except IOError as e:
        print(f"Ошибка при записи в файл '{args.output_file}': {e}")
        return

if __name__ == "__main__":
    main()
