import pytest
from typer.testing import CliRunner
from pathlib import Path
from silo.cli import app
import sys
import json

runner = CliRunner()

def test_install_without_name_local_path(temp_silo_dir, tmp_path):
    """
    REGRESSION: Test 'silo install <path>' without --name flag.
    Should not crash and should use folder name as namespace.
    """
    skill_dir = tmp_path / "bug_skill"
    skill_dir.mkdir()
    (skill_dir / "skill.py").write_text("""# /// script
# requires-python = ">=3.9"
# dependencies = ["silo-framework"]
# ///
from silo import Skill
skill = Skill(namespace='bug_skill')
skill.run()""")
    
    # This crashed due to 'namespace' being None in post-install logic
    result = runner.invoke(app, ["install", str(skill_dir)])
    
    assert result.exit_code == 0
    assert "Successfully installed skill as bug_skill" in result.stdout
    
    # Verify metadata was saved in the temp hub
    hub_path = temp_silo_dir / "hub" / "skills" / "bug_skill"
    assert hub_path.exists()
    assert (hub_path / ".silo_meta.json").exists()

def test_init_scaffolding_has_instructions(temp_silo_dir, tmp_path):
    """
    REGRESSION: Test 'silo init' generates a skill.py with @skill.instructions.
    """
    skill_name = "test_scaffold"
    result = runner.invoke(app, ["init", skill_name, "--path", str(tmp_path)])
    assert result.exit_code == 0
    
    skill_py = tmp_path / skill_name / "skill.py"
    content = skill_py.read_text()
    assert "@skill.instructions()" in content
    assert "def instructions():" in content

def test_inspect_regression(temp_silo_dir, tmp_path):
    """
    Test 'silo inspect' still works after our PYTHONPATH fixes.
    """
    skill_name = "inspect_test"
    skill_dir = tmp_path / skill_name
    skill_dir.mkdir()
    (skill_dir / "skill.py").write_text("""# /// script
# requires-python = ">=3.9"
# dependencies = ["silo-framework"]
# ///
from silo import Skill
skill = Skill(namespace='inspect_test')
@skill.instructions()
def inst(): return "test"
@skill.tool()
def hello(): return "hi"
skill.run()
""")
    
    # Install it
    runner.invoke(app, ["install", str(skill_dir)])
    
    # Inspect it
    result = runner.invoke(app, ["inspect", skill_name])
    assert result.exit_code == 0
    assert skill_name in result.stdout

def test_run_command(temp_silo_dir, tmp_path):
    """Test 'silo run' command."""
    skill_name = "run_test"
    skill_dir = tmp_path / skill_name
    skill_dir.mkdir()
    (skill_dir / "skill.py").write_text("""# /// script
# requires-python = ">=3.9"
# dependencies = ["silo-framework"]
# ///
from silo import Skill, AgentResponse
skill = Skill(namespace='run_test')
@skill.tool()
def echo(msg: str): return AgentResponse(llm_text=msg)
skill.run()
""")
    runner.invoke(app, ["install", str(skill_dir)])
    
    # Run it
    result = runner.invoke(app, ["run", skill_name, "echo", "msg=hello"], catch_exceptions=False)
    if result.exit_code != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    assert result.exit_code == 0
    assert "hello" in result.stdout

def test_search_command(temp_silo_dir):
    """Test 'silo search' command (local)."""
    # Just check if it doesn't crash
    result = runner.invoke(app, ["search", "anything"])
    assert result.exit_code == 0

def test_test_command(temp_silo_dir, tmp_path):
    """Test 'silo test' command."""
    skill_name = "test_cmd_test"
    skill_dir = tmp_path / skill_name
    skill_dir.mkdir()
    (skill_dir / "skill.py").write_text("""# /// script
# requires-python = ">=3.9"
# dependencies = ["silo-framework"]
# ///
from silo import Skill
skill = Skill(namespace='test_cmd_test')
@skill.tool()
def mytest(): return "ok"
skill.run()
""")
    runner.invoke(app, ["install", str(skill_dir)])
    
    # Run test
    result = runner.invoke(app, ["test", skill_name, "mytest"], catch_exceptions=False)
    if result.exit_code != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    assert result.exit_code == 0
    assert "ok" in result.stdout or "Successfully tested" in result.stdout
