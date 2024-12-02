import os
import json
import zlib
from datetime import datetime, timezone
import graphviz  # Используем библиотеку Graphviz

# Путь к конфигурационному файлу по умолчанию
DEFAULT_CONFIG_PATH = 'config.json'

def load_config(config_path=DEFAULT_CONFIG_PATH):
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
        elif line.startswith('committer'):
            # Разбираем строку коммиттера и извлекаем время
            committer_parts = line.split()
            commit_data['committer_timestamp'] = int(committer_parts[-2])  # Временная метка
    
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
    
    # Сортируем коммиты по временной метке
    commits.sort(key=lambda x: x['committer_timestamp'])
    
    return commits

def get_commit_hash_from_ref(branch_ref, repo_path):
    """Получаем хеш коммита, на который указывает ссылка на ветку (например, refs/heads/main)."""
    ref_path = os.path.join(repo_path, '.git', branch_ref)
    with open(ref_path, 'r') as file:
        commit_hash = file.read().strip()
    return commit_hash

def generate_graph(commits):
    """Генерация графа в формате Graphviz (DOT)."""
    graph = graphviz.Digraph(format='png', engine='dot')
    
    # Нумерация коммитов
    for idx, commit in enumerate(commits, 1):
        commit_hash = commit['commit_hash']
        # Используем номер коммита, а не хеш
        graph.node(str(idx), label=f"Commit {idx}\n{commit_hash[:7]}")  # Отображаем номер и первые 7 символов хеша
        
        parent_hash = commit.get('parent')
        if parent_hash:
            # Номер родительского коммита
            parent_idx = next((i for i, c in enumerate(commits, 1) if c['commit_hash'] == parent_hash), None)
            if parent_idx:
                graph.edge(str(parent_idx), str(idx))
    
    return graph

def save_graph_as_png(graph, output_path):
    """Сохранение графа как PNG."""
    graph.render(output_path, view=False)  # Сохраняем граф и не открываем его

def main():
    # Загружаем конфигурацию
    config = load_config()
    
    repo_path = config['repo_path']
    output_path = config['output_image_path']
    commit_date = datetime.strptime(config['commit_date'], "%Y-%m-%d")
    
    # Получаем коммиты после указанной даты
    commits = get_commits_after_date(repo_path, commit_date)
    
    # Генерация графа с помощью Graphviz
    graph = generate_graph(commits)
    
    # Сохранение графа как изображение PNG
    save_graph_as_png(graph, output_path)
    
    print("Graph generated and saved to:", output_path)

if __name__ == "__main__":
    main()
