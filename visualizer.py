import os
import zlib
import sys
import subprocess

def read_git_object(repo_path, object_hash):
    """Reads and decompresses a Git object from the .git/objects directory."""
    object_dir = os.path.join(repo_path, ".git", "objects", object_hash[:2])
    object_file_path = os.path.join(object_dir, object_hash[2:])

    if not os.path.exists(object_file_path):
        raise FileNotFoundError(f"Git object {object_hash} not found in {object_file_path}")

    with open(object_file_path, 'rb') as file:
        compressed_data = file.read()

    return zlib.decompress(compressed_data)

def parse_commit_object(commit_data):
    """Parses a commit object to extract metadata including parent commits and commit message."""
    lines = commit_data.split('\n')
    parents = []
    commit_message = []
    is_message = False

    for line in lines:
        if line.startswith("parent"):
            parents.append(line.split()[1])
        elif line == '':
            is_message = True
        elif is_message:
            commit_message.append(line)

    return parents, "\n".join(commit_message)

def get_branch_head(repo_path, branch_name):
    """Gets the commit hash of the HEAD of the specified branch."""
    heads_dir = os.path.join(repo_path, ".git", "refs", "heads")
    branch_file = os.path.join(heads_dir, branch_name)

    if not os.path.exists(branch_file):
        raise FileNotFoundError(f"Branch {branch_name} not found in {branch_file}")

    with open(branch_file, 'r') as file:
        return file.read().strip()

def traverse_commits(repo_path, start_commit):
    """Traverses commits starting from the given commit hash."""
    visited = set()
    stack = [start_commit]
    commit_graph = {}

    while stack:
        current_commit = stack.pop()
        if current_commit in visited:
            continue

        visited.add(current_commit)
        commit_data = read_git_object(repo_path, current_commit).decode('utf-8')
        parents, message = parse_commit_object(commit_data)
        commit_graph[current_commit] = (parents, message)

        for parent in parents:
            if parent not in visited:
                stack.append(parent)

    return commit_graph

def generate_plantuml(commit_graph):
    """Generates PlantUML text for the commit dependency graph."""
    plantuml_lines = ["@startuml"]

    for commit, (parents, message) in commit_graph.items():
        commit_label = f"{commit[:7]}: {message}".replace('"', '\"')
        plantuml_lines.append(f'"{commit[:7]}: {message.replace("\n", "\\n")}"')
        for parent in parents:
            plantuml_lines.append(f'"{parent[:7]}" --> "{commit[:7]}"')

    plantuml_lines.append("@enduml")
    return "\n".join(plantuml_lines)

def save_plantuml_file(plantuml_text, plantuml_file_path):
    """Saves the PlantUML text to a file."""
    with open(plantuml_file_path, 'w') as file:
        file.write(plantuml_text)

def generate_graph_image(plantuml_file_path, output_image_path, plantuml_jar_path):
    """Generates an image from a PlantUML file using the PlantUML JAR."""
    plantuml_cmd = ['java', '-jar', plantuml_jar_path, plantuml_file_path, '-tpng', '-o', os.path.dirname(output_image_path)]
    result = subprocess.run(plantuml_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Error running PlantUML: {result.stderr}")

def main(repo_path, branch_name, output_image_path, plantuml_jar_path):
    # Get the HEAD commit of the branch
    head_commit = get_branch_head(repo_path, branch_name)

    # Traverse all commits from the branch HEAD
    commit_graph = traverse_commits(repo_path, head_commit)

    # Generate PlantUML text
    plantuml_text = generate_plantuml(commit_graph)

    # Save PlantUML text to a file
    plantuml_file_path = output_image_path.replace('.png', '.puml')
    save_plantuml_file(plantuml_text, plantuml_file_path)

    # Generate the graph image
    generate_graph_image(plantuml_file_path, output_image_path, plantuml_jar_path)

    print(f"Commit dependency graph successfully saved to {output_image_path}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python main.py <repo_path> <branch_name> <output_image_path> <plantuml_jar_path>")
        sys.exit(1)

    repo_path = sys.argv[1]
    branch_name = sys.argv[2]
    output_image_path = sys.argv[3]
    plantuml_jar_path = sys.argv[4]

    try:
        main(repo_path, branch_name, output_image_path, plantuml_jar_path)
    except Exception as e:
        print(f"Ошибка: {e}")
        print(f"Проверяем пути: {repo_path}, {branch_name}, {output_image_path}, {plantuml_jar_path}")
        sys.exit(1)
