#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description="Визуализатор графа зависимостей Git-репозитория.")
    parser.add_argument(
        "-g", "--graphviz-path",
        required=True,
        help="Путь к программе для визуализации графов (Graphviz)."
    )
    parser.add_argument(
        "-r", "--repo-path",
        required=True,
        help="Путь к анализируемому Git-репозиторию."
    )
    parser.add_argument(
        "-o", "--output-file",
        required=True,
        help="Путь к файлу-результату в виде кода Graphviz."
    )
    parser.add_argument(
        "-f", "--target-file",
        required=True,
        help="Имя файла в репозитории для фильтрации коммитов."
    )
    return parser.parse_args()

def verify_graphviz_path(graphviz_path):
    if not os.path.isfile(graphviz_path):
        print(f"Ошибка: Программа для визуализации графов не найдена по пути '{graphviz_path}'.")
        sys.exit(1)
    if not os.access(graphviz_path, os.X_OK):
        print(f"Ошибка: Программа '{graphviz_path}' недоступна для выполнения.")
        sys.exit(1)

def verify_repo_path(repo_path):
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        print(f"Ошибка: Путь '{repo_path}' не является Git-репозиторием.")
        sys.exit(1)

def run_git_command(repo_path, args):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении git команды: {' '.join(e.cmd)}\n{e.stderr}")
        sys.exit(1)

def get_commits_with_file(repo_path, target_file):
    # Получаем список коммитов, изменяющих указанный файл
    commits = run_git_command(repo_path, ["log", "--pretty=format:%H", "--", target_file])
    commit_list = commits.splitlines()
    return commit_list

def get_parent_commits(repo_path, commit):
    parents = run_git_command(repo_path, ["log", "-1", "--pretty=%P", commit])
    if parents:
        return parents.split()
    return []

def get_files_in_commit(repo_path, commit):
    files = run_git_command(repo_path, ["ls-tree", "-r", "--name-only", commit])
    return files.splitlines()

def build_dependency_graph(repo_path, commits):
    graph = {}
    commit_files = {}
    for commit in commits:
        parents = get_parent_commits(repo_path, commit)
        graph[commit] = parents
        files = get_files_in_commit(repo_path, commit)
        commit_files[commit] = files
    return graph, commit_files

def generate_graphviz(graph, commit_files):
    dot = ["digraph G {"]
    dot.append("    node [shape=box, fontsize=10];")
    
    # Создание узлов
    for commit, parents in graph.items():
        # Создаем метку узла с хэшем и списком файлов
        label = f"{commit}"
        files = commit_files.get(commit, [])
        # Ограничим количество отображаемых файлов для читаемости
        if len(files) > 10:
            display_files = files[:10] + ["..."]
        else:
            display_files = files
        files_str = "\\n".join(display_files)
        label += f"\\n{files_str}"
        dot.append(f'    "{commit}" [label="{label}"];')
    
    # Создание ребер
    for commit, parents in graph.items():
        for parent in parents:
            if parent in graph:  # Учитываем только коммиты, включенные в граф
                dot.append(f'    "{commit}" -> "{parent}";')
    
    dot.append("}")
    return "\n".join(dot)

def main():
    args = parse_arguments()
    
    # Проверка путей
    verify_graphviz_path(args.graphviz_path)
    verify_repo_path(args.repo_path)
    
    # Получение коммитов
    commits = get_commits_with_file(args.repo_path, args.target_file)
    if not commits:
        print(f"Коммиты с файлом '{args.target_file}' не найдены.")
        sys.exit(0)
    
    # Построение графа
    graph, commit_files = build_dependency_graph(args.repo_path, commits)
    
    # Генерация Graphviz кода
    graphviz_code = generate_graphviz(graph, commit_files)
    
    # Запись в файл
    try:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(graphviz_code)
        print(f"Graphviz код успешно записан в файл '{args.output_file}'.")
    except IOError as e:
        print(f"Ошибка при записи в файл '{args.output_file}': {e}")
        sys.exit(1)

    # Вывод Graphviz кода на экран
    print("\nСгенерированный Graphviz код:\n")
    print(graphviz_code)

if __name__ == "__main__":
    main()