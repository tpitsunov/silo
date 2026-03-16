import pytest
from typer.testing import CliRunner
import os
import json
from pathlib import Path
from silo.cli import app

runner = CliRunner()

def test_cli_doctor(temp_silo_dir):
    """Test the 'silo doctor' command."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "S.I.L.O Environment Doctor" in result.stdout
    assert "Python Version" in result.stdout

def test_cli_init(temp_silo_dir, tmp_path):
    """Test the 'silo init' command."""
    skill_name = "test_skill"
    # Run init in the temp tmp_path to avoid pollution
    result = runner.invoke(app, ["init", skill_name, "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert f"Successfully initialized skill '{skill_name}'" in result.stdout
    
    skill_dir = tmp_path / skill_name
    assert skill_dir.exists()
    assert (skill_dir / "skill.py").exists()
    assert (skill_dir / ".siloignore").exists()

def test_cli_install_remove(temp_silo_dir, tmp_path):
    """Test installing and then removing a skill via CLI."""
    # 1. Setup a dummy skill
    skill_source = tmp_path / "my_cli_skill.py"
    skill_source.write_text("from silo.skill import Skill\nskill = Skill(namespace='cli_test')")
    
    # 2. Install
    result = runner.invoke(app, ["install", str(skill_source), "--name", "cli_test"])
    assert result.exit_code == 0
    assert "Successfully installed skill as cli_test" in result.stdout
    
    # 3. Check list (ps)
    result = runner.invoke(app, ["ps"])
    assert result.exit_code == 0
    assert "cli_test" in result.stdout
    
    # 4. Remove
    result = runner.invoke(app, ["remove", "cli_test"])
    assert result.exit_code == 0
    assert "Successfully removed 'cli_test' from hub" in result.stdout
    
    # 5. Verify gone
    result = runner.invoke(app, ["ps"])
    assert "cli_test" not in result.stdout

def test_cli_auth_set(temp_silo_dir):
    """Test the 'silo auth set' command."""
    result = runner.invoke(app, ["auth", "set", "MY_TOKEN", "secret-value"])
    assert result.exit_code == 0
    assert "Secret 'MY_TOKEN' encrypted and saved locally" in result.stdout
    
    # Verify it can be loaded
    from silo.security import SecurityManager
    sm = SecurityManager()
    secrets = sm.load_credentials()
    assert secrets["MY_TOKEN"] == "secret-value"
