import json
import os
import re
import urllib.error
import urllib.request
import tomllib
from typing import Any, Dict, List

HTTP_TIMEOUT_SECONDS = 20
ENUMERATE_START = 1


class NuGetError(Exception):
    pass


def _http_get(url: str) -> bytes:
    headers = {"User-Agent": "Mozilla/5.0"}
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(
            request, timeout=HTTP_TIMEOUT_SECONDS
        ) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        msg = f"Не удалось получить данные по адресу {url}: {exc}"
        raise NuGetError(msg) from exc


def load_test_repository(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        msg = f"Тестовый репозиторий не найден: {file_path}"
        raise NuGetError(msg)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        msg = f"Ошибка парсинга JSON: {exc}"
        raise NuGetError(msg) from exc

    if not isinstance(data, dict):
        msg = "Корневой элемент тестового репозитория"
        msg += " должен быть словарем."
        raise NuGetError(msg)

    return data


def collect_dependencies(
    package_name: str,
    repo_url: str,
) -> List[Dict[str, str]]:
    base_url = repo_url.rstrip('/')
    raw_url = base_url.replace("github.com", "raw.githubusercontent.com")
    
    toml_content = None
    for branch in ["main", "master"]:
        url = f"{raw_url}/{branch}/pyproject.toml"
        try:
            toml_content = _http_get(url)
            break
        except NuGetError:
            continue
            
    if not toml_content:
        raise NuGetError(
            "Не удалось найти pyproject.toml в репозитории."
        )

    try:
        data = tomllib.loads(toml_content.decode("utf-8"))
    except Exception as exc:
        raise NuGetError(f"Ошибка парсинга TOML: {exc}") from exc

    dependencies = []
    project = data.get("project", {})
    deps_list = project.get("dependencies", [])

    for dep_str in deps_list:
        match = re.match(r"^([a-zA-Z0-9_-]+)\s*(.*)$", dep_str)
        if match:
            dep_name = match.group(1)
            dep_ver = match.group(2) or "any"
            dep_ver = dep_ver.strip(">=<~^ ,")
            dependencies.append({"id": dep_name, "version": dep_ver})

    return dependencies


def print_dependencies(dependencies: List[Dict[str, str]]) -> None:
    print("Прямые зависимости:")

    if not dependencies:
        print("  Зависимости отсутствуют.")
        return

    for index, dep in enumerate(dependencies, start=ENUMERATE_START):
        print(f"  {index}. {dep['id']} (v{dep['version']})")