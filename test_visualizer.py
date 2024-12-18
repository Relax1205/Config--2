import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import zlib
from visualizer import read_git_object, parse_commit_object, get_branch_head, traverse_commits, generate_plantuml

class TestVisualizer(unittest.TestCase):

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data=zlib.compress(b"commit\ntree 1234567890abcdef\nparent abcdef1234567890\n\nTest commit message\n"))
    def test_read_git_object(self, mock_open, mock_exists):
        """Test reading and decompressing a Git object."""
        repo_path = "fake_repo"
        object_hash = "abcdef1234567890"
        object_data = read_git_object(repo_path, object_hash)
        self.assertIn(b"commit", object_data)
        self.assertIn(b"Test commit message", object_data)

    def test_parse_commit_object(self):
        """Test parsing commit objects."""
        commit_data = """commit\ntree 1234567890abcdef\nparent abcdef1234567890\n\nTest commit message\n"""
        parents, message = parse_commit_object(commit_data)
        self.assertEqual(parents, ["abcdef1234567890"])
        self.assertEqual(message, "Test commit message")

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="abcdef1234567890")
    def test_get_branch_head(self, mock_open, mock_exists):
        """Test getting the HEAD commit of a branch."""
        repo_path = "fake_repo"
        branch_name = "main"
        head_commit = get_branch_head(repo_path, branch_name)
        self.assertEqual(head_commit, "abcdef1234567890")

    @patch("visualizer.read_git_object", return_value=b"commit\ntree 1234567890abcdef\nparent abcdef1234567890\n\nTest commit message\n")
    def test_traverse_commits(self, mock_read_git_object):
        """Test traversing commits starting from a HEAD."""
        repo_path = "fake_repo"
        start_commit = "abcdef1234567890"
        commit_graph = traverse_commits(repo_path, start_commit)
        self.assertIn("abcdef1234567890", commit_graph)
        self.assertEqual(commit_graph["abcdef1234567890"], (["abcdef1234567890"], "Test commit message"))

    def test_generate_plantuml(self):
        """Test generating PlantUML text for the commit graph."""
        commit_graph = {
            "abcdef1": ([], "Initial commit"),
            "1234567": (["abcdef1"], "Second commit"),
        }
        plantuml_text = generate_plantuml(commit_graph)
        self.assertIn("@startuml", plantuml_text)
        self.assertIn("abcdef1", plantuml_text)
        self.assertIn("1234567", plantuml_text)
        self.assertIn("-->", plantuml_text)

    @patch("subprocess.run")
    def test_generate_graph_image(self, mock_subprocess_run):
        """Test generating a PNG image from a PlantUML file."""
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        plantuml_file_path = "test.puml"
        output_image_path = "test.png"
        plantuml_jar_path = "plantuml.jar"

        from visualizer import generate_graph_image
        generate_graph_image(plantuml_file_path, output_image_path, plantuml_jar_path)
        mock_subprocess_run.assert_called_once_with(
            ['java', '-jar', plantuml_jar_path, plantuml_file_path, '-tpng', '-o', os.path.dirname(output_image_path)],
            capture_output=True, text=True
        )

if __name__ == "__main__":
    unittest.main()
