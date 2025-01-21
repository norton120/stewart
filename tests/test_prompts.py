import pytest
from requests.exceptions import HTTPError
from vcr import VCR
from stuart.prompts import get_pypi_package, upsert_function
from stuart.typing import PypiPackage, FileImportModel

vcr = VCR(
    cassette_library_dir="tests/fixtures/vcr_cassettes",
    record_mode="once",
    match_on=["uri", "method"],
    filter_headers=["user-agent", "accept-encoding"],
    ignore_localhost=True,
    serializer="yaml"
)

@pytest.mark.vcr()
def test_get_pypi_package_success():
    """Test successful PyPI package fetch with real API response"""
    result = get_pypi_package("requests")
    assert isinstance(result, PypiPackage)
    assert result.name == "requests"
    assert result.version
    assert result.description

@pytest.mark.vcr()
def test_get_pypi_package_not_found():
    """Test handling of non-existent package"""
    with pytest.raises(HTTPError) as exc_info:
        get_pypi_package("this-package-definitely-does-not-exist")
    assert "404" in str(exc_info.value)

@pytest.mark.vcr()
def test_get_pypi_package_server_error():
    """Test handling of PyPI server error"""
    with pytest.raises(HTTPError):
        # Force a server error by making an invalid request
        get_pypi_package("")


def test_upsert_function_create():
    """Test creating a new function in a new file."""
    imports = [
        {"imported": "List", "from_path": "typing"},
        {"imported": "Optional", "from_path": "typing"}
    ]

    result = upsert_function(
        "src/utils/helpers.py",
        "process_items",
        imports,
        "Process a list of items and return filtered results.",
        "List[str]",
        """def process_items(items: List[str], prefix: Optional[str] = None) -> List[str]:
    if prefix:
        return [i for i in items if i.startswith(prefix)]
    return items"""
    )

    # Check function was created
    assert result.name == "process_items"
    assert result.return_type == "List[str]"
    assert "def process_items" in result.body

def test_upsert_function_update():
    """Test updating an existing function."""
    # First create the function
    imports = [{"imported": "List", "from_path": "typing"}]
    initial = upsert_function(
        "src/utils/helpers.py",
        "process_items",
        imports,
        "Original description",
        "None",
        "def process_items(): pass"
    )

    # Update the function
    updated = upsert_function(
        "src/utils/helpers.py",
        "process_items",
        imports + [{"imported": "Dict", "from_path": "typing"}],
        "Updated description",
        "List[Dict[str, str]]",
        """def process_items() -> List[Dict[str, str]]:
    return [{"key": "value"}]"""
    )

    assert updated.name == "process_items"
    assert updated.description == "Updated description"
    assert updated.return_type == "List[Dict[str, str]]"

def test_upsert_function_normalize_path():
    """Test path normalization when creating function."""
    imports = []
    result = upsert_function(
        "src/utils/helpers",  # No .py extension
        "example",
        imports,
        "Test function",
        "None",
        "def example() -> None: pass"
    )

    assert result.name == "example"
