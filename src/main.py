import argparse
import sys

from config import ConfigError, load_yaml, print_config, validate_params
from nuget import (
    NuGetError,
    collect_dependencies,
    load_test_repository,
    print_dependencies,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Инструмент визуализации графа зависимостей."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        config_data = load_yaml(args.config)
        validate_params(config_data)
        print_config(config_data)

        if config_data["test_mode"]:
            result = load_test_repository(
                config_data["repo_url_or_path"],
                config_data["package_name"],
            )
        else:
            result = collect_dependencies(
                config_data["package_name"],
                config_data["repo_url_or_path"],
            )
        print_dependencies(result)
        print("\nСбор данных успешно завершён.")
    except (ConfigError, NuGetError) as err:
        print(f"Ошибка: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
