import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as et
import zipfile
from io import BytesIO
from typing import Any, Dict, List, Tuple


class NuGetError(Exception):
    pass


def _http_get(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Pract2Var18-Dependency-Collector/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise NuGetError(
            f"Не удалось получить данные по адресу {url}: {exc}"
        ) from exc


def _version_key(version: str) -> Tuple[int, ...]:
    match = re.match(r"^(\d+(?:\.\d+){0,3})", version)
    if not match:
        return (0,)
    return tuple(int(part) for part in match.group(1).split("."))


def _get_package_base_address(source_url: str) -> str:
    data = json.loads(_http_get(source_url).decode("utf-8"))
    resources = data.get("resources", [])
    for resource in resources:
        resource_type = resource.get("@type", "")
        if isinstance(resource_type, list):
            resource_type = " ".join(resource_type)
        if "PackageBaseAddress" in resource_type:
            return resource["@id"].rstrip("/")
    raise NuGetError(
        "В источнике NuGet не найден ресурс PackageBaseAddress."
    )


def _latest_stable_version(base_address: str, package_name: str) -> str:
    package_id = urllib.parse.quote(package_name.lower(), safe="")
    url = f"{base_address}/{package_id}/index.json"
    try:
        data = json.loads(_http_get(url).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NuGetError(
            "Некорректный ответ со списком версий пакета."
        ) from exc

    versions = data.get("versions", [])
    stable = [version for version in versions if "-" not in version]
    if not stable:
        raise NuGetError(
            f"Для пакета '{package_name}' не найдены стабильные версии."
        )
    return max(stable, key=_version_key)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _read_nuspec(package_data: bytes, package_name: str,
                 version: str) -> List[Dict[str, Any]]:
    try:
        with zipfile.ZipFile(BytesIO(package_data)) as archive:
            nuspec_name = next(
                name for name in archive.namelist()
                if name.lower().endswith(".nuspec")
            )
            root = et.fromstring(archive.read(nuspec_name))
    except (zipfile.BadZipFile, StopIteration, et.ParseError, OSError) as exc:
        raise NuGetError(
            "Не удалось прочитать .nuspec из пакета NuGet."
        ) from exc

    dependencies_node = next(
        (node for node in root.iter()
         if _local_name(node.tag) == "dependencies"),
        None,
    )
    if dependencies_node is None:
        return []

    collected: Dict[str, Dict[str, Any]] = {}

    def add_dependency(node: et.Element, framework: str) -> None:
        dep_id = node.attrib.get("id")
        if not dep_id:
            return
        version_range = node.attrib.get("version", "не указана")
        key = dep_id.casefold()
        if key not in collected:
            collected[key] = {
                "id": dep_id,
                "version": version_range,
                "frameworks": [],
            }
        item = collected[key]
        if framework not in item["frameworks"]:
            item["frameworks"].append(framework)
        if item["version"] != version_range:
            item["version"] = "различается по целевым платформам"

    children = list(dependencies_node)
    groups = [node for node in children
              if _local_name(node.tag) == "group"]
    if groups:
        for group in groups:
            framework = group.attrib.get("targetFramework", "любая")
            for dependency in group:
                if _local_name(dependency.tag) == "dependency":
                    add_dependency(dependency, framework)
    else:
        for dependency in children:
            if _local_name(dependency.tag) == "dependency":
                add_dependency(dependency, "любая")

    return sorted(collected.values(), key=lambda item: item["id"].casefold())


def collect_dependencies(package_name: str,
                         source_url: str) -> Dict[str, Any]:
    if not source_url.startswith(("http://", "https://")):
        raise NuGetError(
            "Для обычного режима repo_url_or_path должен быть URL NuGet V3."
        )
    try:
        base_address = _get_package_base_address(source_url)
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
        raise NuGetError(
            "Не удалось разобрать индекс источника NuGet V3."
        ) from exc

    version = _latest_stable_version(base_address, package_name)
    package_id = urllib.parse.quote(package_name.lower(), safe="")
    package_version = urllib.parse.quote(version.lower(), safe="")
    package_url = (
        f"{base_address}/{package_id}/{package_version}/"
        f"{package_id}.{package_version}.nupkg"
    )
    package_data = _http_get(package_url)
    dependencies = _read_nuspec(package_data, package_name, version)
    return {
        "package_name": package_name,
        "version": version,
        "source": source_url,
        "dependencies": dependencies,
    }


def load_test_repository(filepath: str,
                         package_name: str) -> Dict[str, Any]:
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
    except OSError as exc:
        raise NuGetError(
            f"Не удалось открыть тестовый файл: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise NuGetError(
            f"Ошибка формата тестового JSON: {exc}"
        ) from exc

    packages = data.get("packages", {})
    package_data = next(
        (value for key, value in packages.items()
         if key.casefold() == package_name.casefold()),
        None,
    )
    if package_data is None:
        raise NuGetError(
            f"Пакет '{package_name}' отсутствует в тестовом репозитории."
        )

    dependencies = package_data.get("dependencies", [])
    normalized = []
    for dependency in dependencies:
        if not isinstance(dependency, dict) or not dependency.get("id"):
            raise NuGetError(
                "Некорректная запись зависимости в тестовом файле."
            )
        normalized.append({
            "id": dependency["id"],
            "version": dependency.get("version", "не указана"),
            "frameworks": dependency.get(
                "frameworks",
                [dependency.get("target_framework", "любая")],
            ),
        })
    return {
        "package_name": package_name,
        "version": package_data.get("version", "тестовая версия"),
        "source": filepath,
        "dependencies": normalized,
    }


def print_dependencies(result: Dict[str, Any]) -> None:
    print("\nСведения о пакете:")
    print(f"Пакет: {result['package_name']}")
    print(f"Версия: {result['version']}")
    print(f"Источник: {result['source']}")
    dependencies = result["dependencies"]
    print(f"\nПрямые зависимости ({len(dependencies)}):")
    if not dependencies:
        print("Прямые зависимости отсутствуют.")
        return
    for index, dependency in enumerate(dependencies, start=1):
        frameworks = ", ".join(dependency["frameworks"])
        print(
            f"{index}. {dependency['id']} "
            f"(версия: {dependency['version']}; "
            f"платформы: {frameworks})"
        )