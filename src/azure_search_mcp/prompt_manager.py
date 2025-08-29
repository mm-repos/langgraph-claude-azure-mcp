"""Prompt manager for Azure AI Search MCP Server."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from langchain_core.prompts import ChatPromptTemplate


logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompt templates and personas from JSON configuration."""

    def __init__(self, prompts_file: Optional[Union[str, Path]] = None):
        """Initialize the prompt manager."""
        if prompts_file is None:
            prompts_file = Path(__file__).parent / "prompts.json"

        self.prompts_file = Path(prompts_file)
        self.config = self._load_prompts()

    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts configuration from JSON file."""
        try:
            with open(self.prompts_file, encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"Loaded prompts configuration from {self.prompts_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Prompts file not found: {self.prompts_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompts file: {e}")
            raise

    def _format_guiding_principles(self, persona_key: str) -> str:
        """Format guiding principles for a persona into a numbered list."""
        principles = self.config["guiding_principles"].get(persona_key, [])
        formatted_principles = []

        for i, principle in enumerate(principles, 1):
            formatted_principles.append(
                f"{i}.  **{principle['principle']}:** {principle['description']}"
            )

        return "\n".join(formatted_principles)

    def get_persona_info(self, persona_key: str) -> Dict[str, str]:
        """Get persona information."""
        persona = self.config["personas"].get(persona_key, {})
        return {
            "name": persona.get("name", "Unknown"),
            "description": persona.get("description", ""),
            "goals": persona.get("goals", []),
        }

    def create_prompt_template(self, template_key: str) -> ChatPromptTemplate:
        """Create a ChatPromptTemplate for the given template key."""
        template_config = self.config["prompt_templates"].get(template_key)
        if not template_config:
            raise ValueError(f"Prompt template '{template_key}' not found")

        persona_key = template_config["persona"]
        persona_info = self.get_persona_info(persona_key)
        guiding_principles = self._format_guiding_principles(persona_key)

        # Format the template with persona information
        formatted_template = template_config["template"].format(
            persona_name=persona_info["name"],
            persona_description=persona_info["description"],
            guiding_principles=guiding_principles,
        )

        return ChatPromptTemplate.from_template(formatted_template)

    def get_output_format_info(self, format_key: str) -> Dict[str, Any]:
        """Get information about an output format."""
        return self.config["output_formats"].get(format_key, {})

    def get_available_formats(self) -> List[str]:
        """Get list of available output formats."""
        return list(self.config["output_formats"].keys())

    def get_default_format(self) -> str:
        """Get the default output format."""
        for format_key, format_info in self.config["output_formats"].items():
            if format_info.get("default", False):
                return format_key
        return "analysis"  # Fallback default

    def get_prompt_template_for_format(self, format_key: str) -> ChatPromptTemplate:
        """Get the ChatPromptTemplate for a specific output format."""
        format_info = self.get_output_format_info(format_key)
        if not format_info:
            raise ValueError(f"Output format '{format_key}' not found")

        template_key = format_info.get("prompt_template")
        if not template_key:
            raise ValueError(f"No prompt template specified for format '{format_key}'")

        return self.create_prompt_template(template_key)

    def list_personas(self) -> Dict[str, Dict[str, str]]:
        """List all available personas."""
        return {
            key: self.get_persona_info(key) for key in self.config["personas"].keys()
        }

    def list_prompt_templates(self) -> List[str]:
        """List all available prompt templates."""
        return list(self.config["prompt_templates"].keys())

    def reload_prompts(self):
        """Reload prompts from the JSON file."""
        logger.info("Reloading prompts configuration")
        self.config = self._load_prompts()
