"""Enforce the maintained architecture and GitHub Actions contract."""
from pathlib import Path
import ast
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_required_files_and_entry_points():
    for relative in (
        "run.py", "gui.py", "setup.py", "requirements.txt",
        "src/ui/cli.py", "src/ui/gui.py",
        "src/core/ciphers.py", "src/services/cipher_service.py",
        "src/services/file_service.py", "src/ai/analyzer.py",
        ".github/workflows/python-app.yml",
    ):
        assert (ROOT / relative).is_file(), relative


@pytest.mark.parametrize("relative", [
    "cipher_launcher.py", "launch_ciphercraft.bat", "launch_gui.bat",
    "scripts/run_cipher_app.py", "scripts/run_cipher_app.bat",
    "scripts/build_exe.py", "src/core/base.py",
    "CLEANUP_PLAN.md", "CODEBASE_AUDIT.md",
    "IMPLEMENTATION_PLAN.md", "REFACTORING_GUIDE.md",
])
def test_removed_legacy_file_stays_removed(relative):
    assert not (ROOT / relative).exists(), relative


def test_generated_executables_not_tracked():
    # Developers may have a local dist/ after building; only Git tracking matters.
    assert "dist/" in (ROOT / ".gitignore").read_text(encoding="utf-8")
    if (ROOT / ".git").exists():
        files = subprocess.check_output(
            ["git", "ls-files", "--cached", "dist"], cwd=ROOT, text=True
        ).strip()
        assert not files, f"Generated bundles are still tracked:\\n{files}"


def test_ci_configuration_parses_and_has_nine_test_targets():
    # BaseLoader preserves YAML's 'on' key (safe_load uses YAML 1.1 booleans).
    workflow = yaml.load(
        (ROOT / ".github/workflows/python-app.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    assert "pull_request" in workflow["on"]
    assert "main" in workflow["on"]["pull_request"]["branches"]
    jobs = workflow["jobs"]
    assert {"test", "build", "publish"} <= set(jobs)
    assert jobs["build"]["needs"] == "test"
    matrix = jobs["test"]["strategy"]["matrix"]
    assert len(matrix["os"]) == 3
    assert len(matrix["python-version"]) == 3
    assert any("pytest tests/" in step.get("run", "") for step in jobs["test"]["steps"])
    assert any("smoke_executable.py" in step.get("run", "") for step in jobs["build"]["steps"])


def test_packaging_entry_points_are_real():
    setup = (ROOT / "setup.py").read_text(encoding="utf-8")
    assert 'name="ciphercraft"' in setup
    assert "cipher_tool=src.ui.cli:main" in setup
    assert "cipher_gui=src.ui.gui:main" in setup


def test_service_is_not_an_interactive_user_interface():
    source = (ROOT / "src/services/cipher_service.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    top_functions = {node.name for node in module.body if isinstance(node, ast.FunctionDef)}
    assert "main" not in top_functions
    assert "input(" not in source


def test_cli_no_longer_has_legacy_subclass():
    cli = (ROOT / "src/ui/cli.py").read_text(encoding="utf-8")
    assert "class CipherCLI" not in cli
    assert "def main(" in cli
    assert "from src.services.cipher_service import CipherService" in cli


def test_all_cipher_services_exist():
    from src.services.cipher_service import CipherService

    for algorithm in (
        "caesar", "polyalphabetic", "substitution",
        "transposition", "rail_fence", "affine",
    ):
        for action in ("encrypt", "decrypt"):
            assert callable(getattr(CipherService, f"{action}_{algorithm}"))


def test_analyzer_public_entry_points():
    from src.ai.analyzer import CipherAnalyzer

    for name in ("analyze_caesar", "analyze_polyalphabetic", "analyze_with_known_plaintext"):
        assert callable(getattr(CipherAnalyzer, name))
