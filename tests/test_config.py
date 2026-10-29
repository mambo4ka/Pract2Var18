import pytest
from src.config import ConfigError, validate_params


def test_valid_config():
    config = {
        "package_name": "A",
        "repo_url_or_path": "url",
        "test_mode": True,
        "output_filename": "graph.png",
        "max_depth": 3,
    }
    validate_params(config)


def test_missing_parameter():
    config = {"package_name": "A"}
    with pytest.raises(
        ConfigError,
        match="Отсутствует обязательный параметр",
    ):
        validate_params(config)


def test_invalid_max_depth():
    config = {
        "package_name": "A",
        "repo_url_or_path": "url",
        "test_mode": True,
        "output_filename": "graph.png",
        "max_depth": -1,
    }
    with pytest.raises(
        ConfigError,
        match="целым числом >= 0",
    ):
        validate_params(config)