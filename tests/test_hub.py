import pytest
import shutil
import json
from pathlib import Path
from silo.hub import HubManager

def test_hub_directories_creation(temp_silo_dir):
    """Test that HubManager creates necessary directories on init."""
    hm = HubManager()
    assert (temp_silo_dir / "hub" / "skills").exists()
    assert (temp_silo_dir / "hub" / "venvs").exists()

def test_skill_installation_local_file(temp_silo_dir, tmp_path):
    """Test installing a skill from a single .py file."""
    skill_code = "print('hello')"
    skill_file = tmp_path / "myskill.py"
    skill_file.write_text(skill_code)
    
    hm = HubManager()
    hm.install_local(skill_file, "test_namespace")
    
    installed_path = temp_silo_dir / "hub" / "skills" / "test_namespace"
    assert installed_path.exists()
    assert (installed_path / "skill.py").read_text() == skill_code

def test_skill_installation_local_dir(temp_silo_dir, tmp_path):
    """Test installing a skill from a directory."""
    skill_dir = tmp_path / "myskill_dir"
    skill_dir.mkdir()
    (skill_dir / "skill.py").write_text("import os")
    (skill_dir / "README.md").write_text("docs")
    
    hm = HubManager()
    hm.install_local(skill_dir, "dir_namespace")
    
    installed_path = temp_silo_dir / "hub" / "skills" / "dir_namespace"
    assert installed_path.exists()
    assert (installed_path / "skill.py").exists()
    assert (installed_path / "README.md").exists()

def test_skill_removal(temp_silo_dir, tmp_path):
    """Test removing a skill and its environment."""
    hm = HubManager()
    # Mock install
    skill_path = temp_silo_dir / "hub" / "skills" / "to_delete"
    skill_path.mkdir(parents=True)
    venv_path = temp_silo_dir / "hub" / "venvs" / "to_delete"
    venv_path.mkdir(parents=True)
    
    assert hm.is_installed("to_delete")
    
    hm.remove("to_delete")
    
    assert not skill_path.exists()
    assert not venv_path.exists()
    assert not hm.is_installed("to_delete")

def test_metadata_management(temp_silo_dir):
    """Test saving and retrieving skill metadata."""
    hm = HubManager()
    # Mock install
    skill_path = temp_silo_dir / "hub" / "skills" / "meta_test"
    skill_path.mkdir(parents=True)
    
    metadata = {"version": "1.0.0", "tools": {"hello": {}}}
    hm.save_metadata("meta_test", metadata)
    
    meta_file = skill_path / ".silo_meta.json"
    assert meta_file.exists()
    
    with open(meta_file, "r") as f:
        saved_meta = json.load(f)
        assert saved_meta["version"] == "1.0.0"

def test_list_skills(temp_silo_dir):
    """Test listing installed skills."""
    hm = HubManager()
    (temp_silo_dir / "hub" / "skills" / "s1").mkdir(parents=True)
    (temp_silo_dir / "hub" / "skills" / "s2").mkdir(parents=True)
    
    skills = hm.list_skills()
    assert "s1" in skills
    assert "s2" in skills
    assert len(skills) == 2
