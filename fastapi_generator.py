import typer
from typing import List, Dict
import os
from jinja2 import Environment, FileSystemLoader
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import print as rprint

app = typer.Typer()
console = Console()

FEATURES = {
    "docker": "Include Dockerfile and docker-compose.yml",
    "fastapi-cli": "Include FastAPI CLI",
}

PROJECT_STRUCTURE = {
    "app": {
        "__init__.py": "init.py.j2",
        "main.py": "app/main.py.j2",
        "models.py": "app/models.py.j2",
        "crud.py": "app/crud.py.j2",
        "api": {
            "__init__.py": "init.py.j2",
            "main.py": "app/api/main.py.j2",
            "deps.py": "app/api/deps.py.j2",
            "routes": {
                "__init__.py": "init.py.j2",
                "items.py": "app/api/routes/items.py.j2",
            },
        },  
        "core": {
            "__init__.py": "init.py.j2",
            "config.py": "app/core/config.py.j2",
            "db.py": "app/core/db.py.j2",
            "engine.py": "app/core/engine.py.j2",
        },
    },
    "requirements.txt": "requirements.txt.j2",
    "Dockerfile": ("Dockerfile.j2", ["docker"]),
    "docker-compose.yml": ("docker-compose.yml.j2", ["docker"]),
    ".env": ".env.j2",
}

def render_template(template_name: str, context: dict) -> str:
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(template_name)
    return template.render(context)

def create_project_structure(project_name: str, features: List[str], structure: Dict, base_path: str, progress: Progress, task):
    for item, value in structure.items():
        path = os.path.join(base_path, item)
        
        if isinstance(value, dict):
            os.makedirs(path, exist_ok=True)
            create_project_structure(project_name, features, value, path, progress, task)
        else:
            if isinstance(value, tuple):
                template_name, required_features = value
                if not all(feat in features for feat in required_features):
                    continue
            else:
                template_name = value

            content = render_template(template_name, {"project_name": project_name, "features": features})
            with open(path, "w") as f:
                f.write(content)
        
        progress.update(task, advance=1)

@app.command()
def create_project(
    project_name: str = typer.Option(..., prompt=True, help="Name of the project"),
):
    console.print(Panel.fit("🚀 FastAPI Project Generator", style="bold magenta"))
    
    feature_choices = questionary.checkbox(
        "Select features to include:",
        choices=[
            questionary.Choice(
                title=f"{feature} - {description}",
                value=feature
            )
            for feature, description in FEATURES.items()
        ],
        style=questionary.Style([
            ('highlighted', 'fg:cyan bold'),
            ('checkbox', 'fg:cyan'),
            ('checkbox-selected', 'fg:cyan bold'),
        ])
    ).ask()

    total_files = sum(1 for _, v in PROJECT_STRUCTURE.items() if isinstance(v, (str, tuple)))
    for _, v in PROJECT_STRUCTURE.items():
        if isinstance(v, dict):
            total_files += len(v)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
    ) as progress:
        task = progress.add_task("Creating project...", total=total_files)
        
        os.makedirs(project_name, exist_ok=True)
        create_project_structure(project_name, feature_choices, PROJECT_STRUCTURE, project_name, progress, task)

    console.print(f"\n✅ Project '[bold]{project_name}[/bold]' created successfully!")
    console.print("📦 Included features:")
    for feature in feature_choices:
        console.print(f"  • [cyan]{feature}[/cyan]")

if __name__ == "__main__":
    app()
