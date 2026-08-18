---
agent: 'ask'
model: Claude Sonnet 4
description: 'Perform package and security checks on Python projects'
---
* Collect the `pyproject.toml` files in the current directory and check for known vulnerabilities.
* Ensure that the packages below in `required packages` are installed and up to date. If they are not present, install them, if they are outdated, update them to the latest stable versions.
* ALWAYS use `uv` environment to install packages, and never use `pip` directly. If its not installed, install it first using `pip install uv`. On `Mac OS`, use `brew install uv` to install it.
* Check the lines in `required lines` and ensure they are present in the `pyproject.toml` file. If they are not present, add them to the file.
* Ask the user if he wants a `conftest.py` file to be created in the root directory of the project. If yes, create it with the following content:

```python
import pytest
import pathlib
from django.conf import settings
from faker import Faker

BASE_DIR = pathlib.Path(__file__).resolve().parent

fake = Faker()

def pytest_configure(config):
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY=fake.uuid4(),
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
            ],
            AUTH_USER_MODEL='auth.User',
            ROOT_URLCONF='tests.urls',
            DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
            STATIC_URL=BASE_DIR / 'static/',
        )
```

**required packages**

```toml
[dependency-groups]
dev = [
    "autopep8>=2.3.2",
    "coverage>=7.13.4",
    "django-browser-reload>=1.21.0",
    "django-debug-toolbar>=7.0.0",
    "django-watchfiles>=1.4.0",
    "factory-boy>=3.3.3",
    "pytest>=9.0.3",
    "pytest-aio>=2.1.7",
    "pytest-celery>=1.3.0",
    "pytest-cov>=7.1.0",
    "pytest-datafiles>=3.0.1",
    "pytest-django>=4.12.0",
    "pytest-env>=1.6.0",
    "pytest-playwright>=0.7.2",
    "pytest-reportlog>=1.0.0",
    "pytest-timeout>=2.4.0",
    "ruff>=0.15.16",
]
```

**Required lines**

```toml
[tool.pyright]
typeCheckingMode = "off"
reportMissingImports = true
reportUntypedBaseClass = true

[tool.pytest]
testpaths = ["tests"]
timeout="5000"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "api: marks tests as api tests",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.pytest_env]
env_files = [".env", ".env.test"]

[tool.autopep8]
max_line_length = 120
in-place = true
recursive = true
aggressive = 3

[tool.coverage.run]
omit = [
    "manage.py",
    "*/migrations/*",
    "*/__init__.py",
    "*/typings.py"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```

Return the list of packages that were installed or updated, along with their versions.
