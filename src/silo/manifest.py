"""
Manifest generator module.
"""
import inspect
import sys
import os

def generate_manifest(app) -> str:
    """Generates a markdown documentation string for the App."""
    lines = [f"# {app.name}"]
    if app.description:
        lines.append(app.description)
        
    lines.append("\n## Commands")
    
    script_name = "skill.py"
    has_pep723 = False
    
    if sys.argv and sys.argv[0] and os.path.exists(sys.argv[0]):
        script_name = os.path.basename(sys.argv[0])
        try:
            with open(sys.argv[0], "r", encoding="utf-8") as f:
                header = f.read(1024)
                if "# /// script" in header:
                    has_pep723 = True
        except Exception:
            pass
        
    for name, func in app.commands.items():
        lines.append(f"### {name}")
        doc = inspect.getdoc(func) or "No description provided."
        lines.append(f"Description: {doc}")
        
        lines.append("\n**Usage:**")
        
        sig = inspect.signature(func)
        args_strs = []
        schemas = []
        
        for param_name, param in sig.parameters.items():
            param_type_str = f"<{param_name}>"
            
            # Check for Pydantic BaseModel to append schema
            if inspect.isclass(param.annotation):
                try:
                    from pydantic import BaseModel
                    if issubclass(param.annotation, BaseModel):
                        param_type_str = f"'{param_name}_json_string'"
                        schema = param.annotation.model_json_schema()
                        import json
                        schema_str = json.dumps(schema, indent=2)
                        schemas.append(f"**Schema for `{param_name}`:**\n```json\n{schema_str}\n```\n")
                except ImportError:
                    pass
                    
            args_strs.append(f"--{param_name} {param_type_str}")
            
        usage_args = " ".join(args_strs)
        base_cmd = f"uv run {script_name}" if has_pep723 else f"python {script_name}"
        lines.append(f"`{base_cmd} {name} {usage_args}`\n")
        
        if schemas:
            lines.extend(schemas)
        
    return "\n".join(lines).strip()

