import os
import subprocess
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
import git_dependency_visualizer  # замените на реальное имя вашего скрипта

# Тест функции get_commits_with_file
def test_get_commits_with_file_success():
    with patch('git_dependency_visualizer.run_git_command') as mock_run_git_command:
        mock_run_git_command.return_value = "commit1\ncommit2"
        commits = git_dependency_visualizer.get_commits_with_file("repo_path", "file.txt")
        assert commits == ["commit1", "commit2"], f"Expected ['commit1', 'commit2'], but got {commits}"

def test_get_commits_with_file_empty():
    with patch('git_dependency_visualizer.run_git_command') as mock_run_git_command:
        mock_run_git_command.return_value = ""
        commits = git_dependency_visualizer.get_commits_with_file("repo_path", "file.txt")
        assert commits == [], f"Expected [], but got {commits}"

# Тест функции get_parent_commits
def test_get_parent_commits_success():
    with patch('git_dependency_visualizer.run_git_command') as mock_run_git_command:
        mock_run_git_command.return_value = "parent1 parent2"
        parents = git_dependency_visualizer.get_parent_commits("repo_path", "commit_hash")
        assert parents == ["parent1", "parent2"], f"Expected ['parent1', 'parent2'], but got {parents}"

def test_get_parent_commits_empty():
    with patch('git_dependency_visualizer.run_git_command') as mock_run_git_command:
        mock_run_git_command.return_value = ""
        parents = git_dependency_visualizer.get_parent_commits("repo_path", "commit_hash")
        assert parents == [], f"Expected [], but got {parents}"

# Тест функции get_files_in_commit
def test_get_files_in_commit_success():
    with patch('git_dependency_visualizer.run_git_command') as mock_run_git_command:
        mock_run_git_command.return_value = "file1\nfile2"
        files = git_dependency_visualizer.get_files_in_commit("repo_path", "commit_hash")
        assert files == ["file1", "file2"], f"Expected ['file1', 'file2'], but got {files}"

def test_get_files_in_commit_empty():
    with patch('git_dependency_visualizer.run_git_command') as mock_run_git_command:
        mock_run_git_command.return_value = ""
        files = git_dependency_visualizer.get_files_in_commit("repo_path", "commit_hash")
        assert files == [], f"Expected [], but got {files}"

# Тест функции verify_graphviz_path
def test_verify_graphviz_path_valid():
    valid_path = "/path/to/graphviz"
    with patch('os.path.isfile', return_value=True), patch('os.access', return_value=True):
        try:
            git_dependency_visualizer.verify_graphviz_path(valid_path)
        except SystemExit as e:
            assert False, "verify_graphviz_path raised an error with a valid path."

def test_verify_graphviz_path_invalid():
    invalid_path = "/invalid/path/to/graphviz"
    with patch('os.path.isfile', return_value=False):
        try:
            git_dependency_visualizer.verify_graphviz_path(invalid_path)
        except SystemExit:
            pass  # Ожидаем, что ошибка будет вызвана

# Тест функции verify_repo_path
def test_verify_repo_path_valid():
    valid_repo_path = "/valid/repo"
    with patch('os.path.isdir', return_value=True):
        try:
            git_dependency_visualizer.verify_repo_path(valid_repo_path)
        except SystemExit as e:
            assert False, "verify_repo_path raised an error with a valid repo."

def test_verify_repo_path_invalid():
    invalid_repo_path = "/invalid/repo"
    with patch('os.path.isdir', return_value=False):
        try:
            git_dependency_visualizer.verify_repo_path(invalid_repo_path)
        except SystemExit:
            pass  # Ожидаем, что ошибка будет вызвана

# Тест функции run_git_command
def test_run_git_command_success():
    with patch('git_dependency_visualizer.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout="output", stderr="")
        result = git_dependency_visualizer.run_git_command("repo_path", ["log"])
        assert result == "output", f"Expected 'output', but got {result}"

def test_run_git_command_failure():
    with patch('git_dependency_visualizer.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git", output="error", stderr="error")
        try:
            git_dependency_visualizer.run_git_command("repo_path", ["log"])
        except SystemExit:
            pass  # Ожидаем, что ошибка будет вызвана

# Тест функции generate_graphviz
def test_generate_graphviz():
    graph = {"commit1": ["parent1"], "commit2": ["parent2"]}
    commit_files = {"commit1": ["file1"], "commit2": ["file2"]}
    graphviz_code = git_dependency_visualizer.generate_graphviz(graph, commit_files)
    
    # Проверка на наличие коммитов и связей с родителями
    assert "commit1" in graphviz_code, "commit1 не найден в коде Graphviz"
    assert "parent1" in graphviz_code, "parent1 не найден в коде Graphviz"
    assert "commit2" in graphviz_code, "commit2 не найден в коде Graphviz"
    assert "parent2" in graphviz_code, "parent2 не найден в коде Graphviz"

# Тест функции parse_arguments
def test_parse_arguments():
    test_args = ["script.py", "-g", "/path/to/graphviz", "-r", "/path/to/repo", "-o", "output.dot", "-f", "file.txt"]
    with patch.object(sys, 'argv', test_args):
        args = git_dependency_visualizer.parse_arguments()
        assert args.graphviz_path == "/path/to/graphviz", f"Expected '/path/to/graphviz', but got {args.graphviz_path}"
        assert args.repo_path == "/path/to/repo", f"Expected '/path/to/repo', but got {args.repo_path}"
        assert args.output_file == "output.dot", f"Expected 'output.dot', but got {args.output_file}"
        assert args.target_file == "file.txt", f"Expected 'file.txt', but got {args.target_file}"

# Запуск всех тестов
def run_tests():
    test_get_commits_with_file_success()
    test_get_commits_with_file_empty()
    test_get_parent_commits_success()
    test_get_parent_commits_empty()
    test_get_files_in_commit_success()
    test_get_files_in_commit_empty()
    test_verify_graphviz_path_valid()
    test_verify_graphviz_path_invalid()
    test_verify_repo_path_valid()
    test_verify_repo_path_invalid()
    test_run_git_command_success()
    test_run_git_command_failure()
    test_generate_graphviz()
    test_parse_arguments()

    print("Все тесты прошли успешно.")

# Запуск тестов
if __name__ == "__main__":
    run_tests()
