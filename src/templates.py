from pathlib import Path
from string import Template


def load_prompt_template(filename: str) -> Template:
    """Load a prompt template from the prompts directory"""
    return Template(Path(f"prompts/{filename}").read_text())


def load_prompt_text(filename: str) -> str:
    """Load prompt text from the prompts directory"""
    return Path(f"prompts/{filename}").read_text().strip()
