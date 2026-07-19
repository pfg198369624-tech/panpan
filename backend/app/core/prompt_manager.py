from pathlib import Path
from typing import Optional


class PromptManager:
    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            prompts_dir = str(Path(__file__).parent.parent.parent / "prompts")
        self.prompts_dir = Path(prompts_dir)

    def load(self, name: str, version: str = "v1") -> str:
        filepath = self.prompts_dir / f"{name}_{version}.md"
        if not filepath.exists():
            raise FileNotFoundError(f"Prompt file not found: {filepath}")
        return filepath.read_text(encoding="utf-8")

    def render(self, name: str, version: str, **kwargs) -> str:
        template = self.load(name, version)
        return template.format(**kwargs)


prompt_manager = PromptManager()
