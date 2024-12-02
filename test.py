import os
import json
import struct
import zlib
from datetime import datetime, timezone

# Функции из вашего оригинального скрипта
def load_config(config_path='config.json'):
    """Загрузка конфигурации из JSON-файла."""
    with open(config_path, 'r') as file:
        return json.load(file)

def read_commit(commit_hash, repo_path):
    """Чтение коммита по хешу из репозитория."""
    objects_path = os.path.join(repo_path, '.git', 'objects')
    
    # Проверяем, что хеш имеет правильный формат (например, 40 символов)
    if len(commit_hash) < 40:
        raise ValueError(f"Invalid commit hash length: {commit_hash}")
    
    object_dir = commit_hash[:2]  # Первые два символа хеша — это подкаталог
    object_file = commit_hash[2:]  # Остальная часть хеша — это имя файла
    commit_file_path = os.path.join(objects_path, object_dir, object_file)
    
    print(f"Trying to read commit from: {commit_file_path}")  # Отладочная информация
    
    # Проверка наличия файла
    if not os.path.exists(commit_file_path):
        raise FileNotFoundError(f"Git object file not found: {commit_file_path}")
    
    # Чтение сжатыми данными и распаковка
    with open(commit_file_path, 'rb') as file:
        file_content = file.read()
    
    # Разжимаем с помощью zlib
    decompressed_data = zlib.decompress(file_content)
    
    # Теперь распарсим декодированные данные
    return parse_commit_data(decompressed_data, commit_hash)

def parse_commit_data(data, commit_hash):
    """Парсинг данных коммита."""
    commit_data = {'commit_hash': commit_hash}  # Добавляем хеш коммита
    lines = data.decode('utf-8').split('\n')
    
    # Парсим коммит
    for line in lines:
        if line.startswith('parent'):
            commit_data['parent'] = line.split()[1]
        elif line.startswith('author'):
            commit_data['author'] = line.split()[1]
        elif line.startswith('committer'):
            # Разбираем строку коммиттера и извлекаем время
            committer_parts = line.split()
            commit_data['committer'] = committer_parts[1]  # Имя
            commit_data['committer_email'] = committer_parts[2]  # Электронная почта
            commit_data['committer_timestamp'] = int(committer_parts[-2])  # Временная метка
        elif line.startswith('tree'):
            commit_data['tree'] = line.split()[1]
        elif line.startswith('message'):
            commit_data['message'] = line.split()[1]
    
    return commit_data

def get_commits_after_date(repo_path, start_date):
    """Получение всех коммитов после указанной даты."""
    commits = []
    
    # Прочитаем объект HEAD, чтобы получить ссылку на текущую ветку
    head_path = os.path.join(repo_path, '.git', 'HEAD')
    with open(head_path, 'r') as head_file:
        ref = head_file.read().strip()
        # Извлекаем хеш коммита из ветки (например, refs/heads/main)
        if ref.startswith("ref:"):
            branch_ref = ref.split()[1]
            branch_commit_hash = get_commit_hash_from_ref(branch_ref, repo_path)
        else:
            # Если по какой-то причине HEAD не ссылается на ветку, попробуем взять текущий коммит
            branch_commit_hash = ref
    
    # Инициализируем чтение коммитов начиная с HEAD
    current_commit_hash = branch_commit_hash
    while current_commit_hash:
        commit_data = read_commit(current_commit_hash, repo_path)
        commit_date = datetime.fromtimestamp(commit_data['committer_timestamp'], timezone.utc)
        
        # Приводим start_date к временному поясу UTC
        start_date = start_date.replace(tzinfo=timezone.utc)
        
        if commit_date >= start_date:
            commits.append(commit_data)
        
        # Переходим к родительскому коммиту
        current_commit_hash = commit_data.get('parent', None)
        if not current_commit_hash:
            break
    
    return commits

def get_commit_hash_from_ref(branch_ref, repo_path):
    """Получаем хеш коммита, на который указывает ссылка на ветку (например, refs/heads/main)."""
    ref_path = os.path.join(repo_path, '.git', branch_ref)
    with open(ref_path, 'r') as file:
        commit_hash = file.read().strip()
    return commit_hash

def generate_graph(commits):
    """Генерация графа в формате Graphviz (DOT)."""
    import graphviz
    graph = graphviz.Digraph(format='png', engine='dot')
    
    for commit in commits:
        commit_hash = commit['commit_hash']
        commit_message = commit['message'] if 'message' in commit else 'No message'
        graph.node(commit_hash, label=f"{commit_hash[:7]}\n{commit_message}")
        
        parent_hash = commit.get('parent')
        if parent_hash:
            graph.edge(parent_hash, commit_hash)
    
    return graph

def save_graph_as_png(graph, output_path):
    """Сохранение графа как PNG."""
    graph.render(output_path, view=False)  # Сохраняем граф и не открываем его

# Тесты для функций

def test_load_config():
    config = load_config("test_config.json")
    assert config is not None, "Failed to load config"
    assert 'repo_path' in config, "repo_path missing in config"
    assert 'output_image_path' in config, "output_image_path missing in config"
    print("test_load_config passed!")

def test_read_commit():
    # Мокаем функцию zlib.decompress
    commit_hash = "abc1234567890def1234567890abcdef12345678"  # 40 символов
    repo_path = "/mock/path/to/repo"
    
    # Мокаем содержимое файла
    commit_data = b"tree abc123\nparent def456\nauthor John Doe <john@example.com> 1625827216 +0000\ncommitter John Doe <john@example.com> 1625827216 +0000\nmessage Initial commit"
    
    # Мокаем функцию zlib.decompress
    def mock_decompress(data):
        return commit_data
    
    zlib.decompress = mock_decompress  # Замещаем стандартную функцию

    result = read_commit(commit_hash, repo_path)
    
    assert result['commit_hash'] == commit_hash, "Test failed: commit_hash mismatch"
    assert result['parent'] == "def456", "Test failed: parent commit mismatch"
    assert result['committer_timestamp'] == 1625827216, "Test failed: committer timestamp mismatch"
    assert result['message'] == "Initial commit", "Test failed: message mismatch"
    
    print("test_read_commit passed!")

def test_generate_graph():
    commits = [
        {'commit_hash': 'abc1234567890def1234567890abcdef12345678', 'message': 'Initial commit', 'parent': None},
        {'commit_hash': 'def4567890abcdef1234567890abcdef12345678', 'message': 'Second commit', 'parent': 'abc1234567890def1234567890abcdef12345678'}
    ]
    
    graph = generate_graph(commits)
    assert graph is not None, "Failed to generate graph"
    
    # Проверяем, что в графе есть все узлы и связи
    assert 'abc1234567890def1234567890abcdef12345678' in graph.source, "Commit hash abc1234567890def1234567890abcdef12345678 not found in graph"
    assert 'def4567890abcdef1234567890abcdef12345678' in graph.source, "Commit hash def4567890abcdef1234567890abcdef12345678 not found in graph"
    
    print("test_generate_graph passed!")

def run_tests():
    test_load_config()
    test_read_commit()
    test_generate_graph()

if __name__ == "__main__":
    run_tests()
