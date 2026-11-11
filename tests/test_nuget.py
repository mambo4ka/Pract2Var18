import io
import json
import zipfile

from src import nuget


def make_package():
    content = """<?xml version="1.0"?>
    <package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
      <metadata>
        <id>Sample.Package</id>
        <version>1.0.0</version>
        <dependencies>
          <group targetFramework=".NETStandard2.0">
            <dependency id="Alpha" version="[1.0, )" />
            <dependency id="Beta" version="2.0" />
          </group>
          <group targetFramework="net8.0">
            <dependency id="Alpha" version="[1.0, )" />
            <dependency id="Gamma" version="3.0" />
          </group>
        </dependencies>
      </metadata>
    </package>"""
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("Sample.Package.nuspec", content)
    return output.getvalue()


def test_read_nuspec_collects_direct_dependencies():
    result = nuget._read_nuspec(make_package(), "Sample.Package", "1.0.0")
    assert [item["id"] for item in result] == ["Alpha", "Beta", "Gamma"]
    alpha = result[0]
    assert alpha["frameworks"] == [".NETStandard2.0", "net8.0"]


def test_read_nuspec_without_dependencies():
    package = b""
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(
            "Empty.nuspec",
            '<package><metadata><id>Empty</id></metadata></package>',
        )
    assert nuget._read_nuspec(output.getvalue(), "Empty", "1.0") == []


def test_load_test_repository(tmp_path):
    fixture = {
        "packages": {
            "Demo": {
                "version": "1.2.0",
                "dependencies": [{"id": "Library", "version": ">= 2.0"}],
            }
        }
    }
    path = tmp_path / "repository.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")
    result = nuget.load_test_repository(str(path), "demo")
    assert result["version"] == "1.2.0"
    assert result["dependencies"][0]["id"] == "Library"


def test_collect_dependencies_uses_latest_stable(monkeypatch):
    package = make_package()
    responses = {
        "https://feed.test/index.json": json.dumps({
            "resources": [{
                "@type": "PackageBaseAddress/3.0.0",
                "@id": "https://feed.test/flat",
            }]
        }).encode(),
        "https://feed.test/flat/sample.package/index.json": json.dumps({
            "versions": ["1.0.0-beta", "1.0.0", "1.2.0"]
        }).encode(),
        (
            "https://feed.test/flat/sample.package/1.2.0/"
            "sample.package.1.2.0.nupkg"
        ): package,
    }

    def fake_get(url):
        return responses[url]

    monkeypatch.setattr(nuget, "_http_get", fake_get)
    result = nuget.collect_dependencies(
        "Sample.Package", "https://feed.test/index.json"
    )
    assert result["version"] == "1.2.0"
    assert len(result["dependencies"]) == 3