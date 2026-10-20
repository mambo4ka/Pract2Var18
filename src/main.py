import argparse
import sys

from config import ConfigError, load_yaml, print_config, validate_params


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Инструмент визуализации графа зависимостей."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Путь к YAML конфигурации"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        config_data = load_yaml(args.config)
        validate_params(config_data)
        print_config(config_data)
    except ConfigError as err:
        print(f"Ошибка конфигурации: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()