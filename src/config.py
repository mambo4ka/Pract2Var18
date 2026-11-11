import os
from typing import Any, Dict

import yaml

MIN_DEPTH = 0


class ConfigError(Exception):
    pass


def load_yaml(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        raise ConfigError(f"Файл конфигурации не найден: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Ошибка парсинга YAML: {exc}") from exc

    if not isinstance(config, dict):
        msg = "Корневой элемент конфигурации должен быть словарем."
        raise ConfigError(msg)

    return config


def validate_params(config: Dict[str, Any]) -> None:
    required_params = [
        "package_name",
        "repo_url_or_path",
        "test_mode",
        "max_depth",
    ]
    for param in required_params:
        if param not in config:
            msg = f"Отсутствует обязательный параметр: '{param}'"
            raise ConfigError(msg)

    if (
        not isinstance(config["package_name"], str)
        or not config["package_name"]
    ):
        msg = "Параметр 'package_name' должен быть непустой строкой."
        raise ConfigError(msg)

    if (
        not isinstance(config["repo_url_or_path"], str)
        or not config["repo_url_or_path"]
    ):
        msg = "Параметр 'repo_url_or_path' должен быть непустой строкой."
        raise ConfigError(msg)

    if not isinstance(config["test_mode"], bool):
        msg = "Параметр 'test_mode' должен быть булевым значением."
        raise ConfigError(msg)

    max_depth = config["max_depth"]
    if not isinstance(max_depth, int) or max_depth < MIN_DEPTH:
        msg = f"Параметр 'max_depth' должен быть >= {MIN_DEPTH}."
        raise ConfigError(msg)


def print_config(config: Dict[str, Any]) -> None:
    print("Текущие настройки:")
    for key, value in config.items():
        print(f"  {key} = {value}")