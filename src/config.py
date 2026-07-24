"""
Configuration module for Tipitaka PTS Browser.

This module handles application configuration, including:
- Default settings
- Path configuration
- Environment variables
- Configuration validation
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union


class Config:
    """Configuration manager for Tipitaka PTS Browser."""

    # Default configuration
    DEFAULT_CONFIG = {
        "application": {
            "name": "Tipitaka PTS Browser",
            "version": "1.0.0",
            "author": "Tipitaka PTS Browser Team",
            "license": "GPL-3.0",
        },
        "paths": {
            "data_dir": "data",
            "dict_dir": "data/dictionaries",
            "docs_dir": "docs",
            "qml_dir": "qml",
            "logs_dir": "logs",
            "cache_dir": "cache",
        },
        "ui": {
            "language": "en",
            "theme": "light",
            "font_size": 12,
            "font_family": "Noto Sans",
            "show_line_numbers": True,
            "word_wrap": True,
            "auto_save": True,
            "recent_files_limit": 10,
        },
        "text": {
            "default_edition": "PTS",
            "available_editions": ["PTS", "MYANMAR", "VRI", "THAI", "SINHALA"],
            "line_length": 80,
            "paragraph_spacing": 1.5,
            "show_metadata": True,
            "highlight_search": True,
        },
        "search": {
            "case_sensitive": False,
            "whole_word": False,
            "regex": False,
            "fuzzy_match": True,
            "fuzzy_threshold": 0.8,
            "max_results": 100,
            "search_history_limit": 50,
        },
        "dictionary": {
            "default_dictionary": "critical-pali-dictionary",
            "show_etymology": True,
            "show_examples": True,
            "show_pronunciation": False,
            "auto_lookup": False,
        },
        "bookmarks": {
            "auto_save": True,
            "max_bookmarks": 1000,
            "export_format": "json",
            "group_by_text": True,
        },
        "export": {
            "default_format": "pdf",
            "formats": ["pdf", "html", "txt", "json", "csv"],
            "include_metadata": True,
            "include_line_numbers": True,
            "preserve_formatting": True,
        },
        "performance": {
            "cache_size": 100,
            "preload_texts": False,
            "lazy_loading": True,
            "worker_threads": 2,
            "memory_limit": 1024,  # MB
        },
        "network": {
            "check_updates": True,
            "update_channel": "stable",
            "proxy_enabled": False,
            "proxy_host": "",
            "proxy_port": 8080,
            "timeout": 30,
        },
        "logging": {
            "level": "INFO",
            "file": "tipitaka.log",
            "max_size": 10485760,  # 10 MB
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }

    # Environment variable mappings
    ENV_VARS = {
        "TIPITAKA_DATA_DIR": "paths.data_dir",
        "TIPITAKA_LANGUAGE": "ui.language",
        "TIPITAKA_THEME": "ui.theme",
        "TIPITAKA_EDITION": "text.default_edition",
        "TIPITAKA_LOG_LEVEL": "logging.level",
    }

    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize configuration.

        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        self.config_file = self._resolve_config_file(config_file)
        self.config = self.DEFAULT_CONFIG.copy()
        self._user_config = {}
        self._load_config()

    def _resolve_config_file(self, config_file: Optional[Union[str, Path]]) -> Path:
        """Resolve configuration file path."""
        if config_file:
            return Path(config_file)

        # Default locations (in order of preference)
        default_locations = [
            # User configuration directory
            Path.home() / ".config" / "tipitaka-pts-browser" / "config.json",
            # Application directory
            Path(__file__).parent / "config.json",
            # Current working directory
            Path.cwd() / "tipitaka-config.json",
        ]

        for location in default_locations:
            if location.exists():
                return location

        # If no config file exists, use the user config directory
        return default_locations[0]

    def _load_config(self):
        """Load configuration from file and environment variables."""
        # Load from file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._user_config = json.load(f)
                    self._merge_configs()
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")

        # Apply environment variables
        self._apply_env_vars()

        # Resolve paths
        self._resolve_paths()

    def _merge_configs(self):
        """Merge user configuration with defaults."""

        def merge_dicts(base: Dict, override: Dict) -> Dict:
            """Recursively merge dictionaries."""
            result = base.copy()
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            return result

        self.config = merge_dicts(self.config, self._user_config)

    def _apply_env_vars(self):
        """Apply environment variable overrides."""
        for env_var, config_path in self.ENV_VARS.items():
            value = os.environ.get(env_var)
            if value is not None:
                self._set_nested_value(config_path, value)

    def _set_nested_value(self, path: str, value: Any):
        """Set a nested value in the configuration using dot notation."""
        keys = path.split(".")
        config = self.config

        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        last_key = keys[-1]

        # Convert value type based on existing value
        if last_key in config:
            existing_value = config[last_key]
            if isinstance(existing_value, bool):
                value = str(value).lower() in ("true", "1", "yes", "on")
            elif isinstance(existing_value, int):
                try:
                    value = int(value)
                except ValueError:
                    pass
            elif isinstance(existing_value, float):
                try:
                    value = float(value)
                except ValueError:
                    pass
            elif isinstance(existing_value, list):
                value = [item.strip() for item in str(value).split(",")]

        config[last_key] = value

    def _resolve_paths(self):
        """Resolve relative paths to absolute paths."""
        base_dir = Path(__file__).parent

        for path_key in [
            "data_dir",
            "dict_dir",
            "docs_dir",
            "qml_dir",
            "logs_dir",
            "cache_dir",
        ]:
            path_value = self.get(f"paths.{path_key}")
            if path_value and not Path(path_value).is_absolute():
                self.set(f"paths.{path_key}", str(base_dir / path_value))

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot notation.

        Args:
            key: Configuration key in dot notation (e.g., "ui.language")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any, save: bool = False):
        """
        Set configuration value by dot notation.

        Args:
            key: Configuration key in dot notation
            value: Value to set
            save: Whether to save to file immediately
        """
        self._set_nested_value(key, value)

        if save:
            self.save()

    def save(self, config_file: Optional[Union[str, Path]] = None):
        """
        Save configuration to file.

        Args:
            config_file: File to save to. If None, uses current config file.
        """
        if config_file:
            self.config_file = Path(config_file)

        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._user_config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving config file {self.config_file}: {e}")

    def reset(self, section: Optional[str] = None):
        """
        Reset configuration to defaults.

        Args:
            section: Specific section to reset. If None, resets entire config.
        """
        if section:
            if section in self.DEFAULT_CONFIG:
                self.config[section] = self.DEFAULT_CONFIG[section].copy()
                if section in self._user_config:
                    del self._user_config[section]
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self._user_config = {}

    def validate(self) -> Dict[str, list]:
        """
        Validate configuration.

        Returns:
            Dictionary of validation errors by section
        """
        errors = {}

        # Validate paths
        for path_key in ["data_dir", "qml_dir"]:
            path = self.get(f"paths.{path_key}")
            if path and not Path(path).exists():
                errors.setdefault("paths", []).append(
                    f"Directory does not exist: {path}"
                )

        # Validate UI settings
        font_size = self.get("ui.font_size")
        if not isinstance(font_size, (int, float)) or font_size < 6 or font_size > 72:
            errors.setdefault("ui", []).append(f"Invalid font size: {font_size}")

        # Validate text settings
        edition = self.get("text.default_edition")
        available = self.get("text.available_editions", [])
        if edition not in available:
            errors.setdefault("text", []).append(
                f"Default edition '{edition}' not in available editions"
            )

        # Validate search settings
        threshold = self.get("search.fuzzy_threshold")
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            errors.setdefault("search", []).append(
                f"Invalid fuzzy threshold: {threshold}"
            )

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self.config.copy()

    def __str__(self) -> str:
        """String representation of configuration."""
        return json.dumps(self.config, indent=2, ensure_ascii=False)


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config(config_file: Optional[Union[str, Path]] = None) -> Config:
    """
    Get or create global configuration instance.

    Args:
        config_file: Configuration file path

    Returns:
        Configuration instance
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = Config(config_file)

    return _config_instance


def init_config(config_file: Optional[Union[str, Path]] = None) -> Config:
    """
    Initialize and return configuration.

    Args:
        config_file: Configuration file path

    Returns:
        Configuration instance
    """
    return get_config(config_file)


if __name__ == "__main__":
    # Test the configuration
    config = Config()
    print("Current configuration:")
    print(config)

    # Test validation
    errors = config.validate()
    if errors:
        print("\nValidation errors:")
        for section, section_errors in errors.items():
            print(f"  {section}:")
            for error in section_errors:
                print(f"    - {error}")
    else:
        print("\nConfiguration is valid!")
