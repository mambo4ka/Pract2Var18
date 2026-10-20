import os
from typing import Any, Dict

import yaml


class ConfigError(Exception):
    pass


def load_yaml(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        raise ConfigError(f"Файл конфигурации не найден: {filepath}")

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Ошибка синтаксиса YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("Корневой элемент YAML должен быть словарем.")
    return data


def validate_params(config: Dict[str, Any]) -> None:
    required_keys = [
        "package_name", "repo_url_or_path", "test_mode",
        "output_filename", "max_depth"
    ]
    for key in required_keys:
        if key not in config:
            raise ConfigError(f"Отсутствует обязательный параметр: {key}")

    if not isinstance(config["package_name"], str) or not config["package_name"]:
        raise ConfigError("Параметр 'package_name' должен быть строкой.")

    if not isinstance(config["repo_url_or_path"], str):
        raise ConfigError("Параметр 'repo_url_or_path' должен быть строкой.")

    if not isinstance(config["test_mode"], bool):
        raise ConfigError("Параметр 'test_mode' должен быть boolean (true/false).")

    if not isinstance(config["output_filename"], str):
        raise ConfigError("Параметр 'output_filename' должен быть строкой.")

    if not isinstance(config["max_depth"], int) or config["max_depth"] < 0:
        raise ConfigError("Параметр 'max_depth' должен быть целым числом >= 0.")


def print_config(config: Dict[str, Any]) -> None:
    print("Загруженные параметры конфигурации:")
    for key, value in config.items():
        print(f"{key}: {value}")