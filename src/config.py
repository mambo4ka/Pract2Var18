import os
from typing import Any, Dict

import yaml


class ConfigError(Exception):
    pass


def load_yaml(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        msg = f"Файл конфигурации не найден: {filepath}"
        raise ConfigError(msg)

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        msg = f"Ошибка синтаксиса YAML: {exc}"
        raise ConfigError(msg) from exc

    if not isinstance(data, dict):
        msg = "Корневой элемент YAML должен быть словарем."
        raise ConfigError(msg)
    return data


def validate_params(config: Dict[str, Any]) -> None:
    required_keys = [
        "package_name",
        "repo_url_or_path",
        "test_mode",
        "output_filename",
        "max_depth",
    ]
    for key in required_keys:
        if key not in config:
            msg = f"Отсутствует обязательный параметр: {key}"
            raise ConfigError(msg)

    package_name = config["package_name"]
    if not isinstance(package_name, str) or not package_name:
        msg = "Параметр 'package_name' должен быть строкой."
        raise ConfigError(msg)

    if not isinstance(config["repo_url_or_path"], str):
        msg = "Параметр 'repo_url_or_path' должен быть строкой."
        raise ConfigError(msg)

    if not isinstance(config["test_mode"], bool):
        msg = "Параметр 'test_mode' должен быть true/false."
        raise ConfigError(msg)

    if not isinstance(config["output_filename"], str):
        msg = "Параметр 'output_filename' должен быть строкой."
        raise ConfigError(msg)

    max_depth = config["max_depth"]
    if not isinstance(max_depth, int) or max_depth < 0:
        msg = "Параметр 'max_depth' должен быть целым числом >= 0."
        raise ConfigError(msg)


def print_config(config: Dict[str, Any]) -> None:
    print("Загруженные параметры конфигурации:")
    for key, value in config.items():
        print(f"{key}: {value}")