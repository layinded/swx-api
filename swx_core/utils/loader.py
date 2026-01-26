"""
Module Loader
-------------
This module dynamically loads and imports:
- Models, services, repositories, and middleware from both `core/` and `app/` directories.
- Middleware components that define an `apply_middleware(app: FastAPI)` function.

Features:
- Recursively imports all submodules in specified directories.
- Reloads already imported modules for real-time updates.
- Ensures middleware is loaded properly in FastAPI applications.

Functions:
- `dynamic_import()`: Dynamically imports all modules within a specified path.
- `load_all_modules()`: Loads models, services, repositories, and middleware dynamically.
- `load_middleware()`: Loads and applies middleware to a FastAPI application.
"""

import importlib
import pkgutil
import sys
from pathlib import Path
import traceback
from typing import Dict, Any

from fastapi import FastAPI

from swx_core.middleware.logging_middleware import logger
from swx_core.middleware.session_middleware import setup_session_middleware


def dynamic_import(base_path: str, package_name: str, recursive: bool = False) -> Dict[str, Any]:
    """
    Dynamically imports all modules within the given `base_path` and associates them with the specified `package_name`.

    Args:
        base_path (str): The base directory path to search for modules.
        package_name (str): The package name associated with the base path.
        recursive (bool, optional): Whether to recursively import submodules. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary where keys are module names and values are imported modules.

    Behavior:
    - Ensures that modules are reloaded if already imported.
    - Supports recursive importing of submodules.
    - Handles OS-specific paths.
    - Logs errors for failed imports.

    Example:
        `dynamic_import("swx_app/models", "swx_app.models")`
    """
    imported_modules = {}
    package_path = Path(base_path).resolve()  # Get absolute path

    if not package_path.exists():
        logger.warning(f"No user-defined API routes found in `{base_path}`.")
        return imported_modules

    for finder, mod_name, is_pkg in pkgutil.iter_modules([str(package_path)]):
        full_module_name = f"{package_name}.{mod_name}"

        try:
            # Skip reload for model modules: re-execution re-registers tables and raises
            # "Table 'X' is already defined for this MetaData instance".
            skip_reload = ".models." in full_module_name

            if full_module_name in sys.modules:
                if not skip_reload:
                    importlib.reload(sys.modules[full_module_name])
                    logger.info(f"Reloaded module: {full_module_name}")
            else:
                module = importlib.import_module(full_module_name)
                sys.modules[full_module_name] = module
                logger.info(f"Loaded new module: {full_module_name}")

            # Store using full module name as key
            imported_modules[full_module_name] = sys.modules[full_module_name]

            # Recursive Import for Nested Folders
            if recursive and is_pkg:
                subdir_path = package_path / mod_name
                subpackage_name = full_module_name  # Keep full package path
                submodules = dynamic_import(str(subdir_path), subpackage_name, recursive=True)
                imported_modules.update(submodules)

        except Exception as e:
            logger.error(f"Error loading {full_module_name}: {e}\n{traceback.format_exc()}")

    return imported_modules


def load_all_modules() -> None:
    """
    Loads models, services, repositories, and middleware dynamically from both `swx_core/` and `swx_app/`.

    Logs:
        - Number of loaded modules from each package.

    Example:
        `load_all_modules()` -> Loads all components dynamically at startup.
    """
    directories = {
        "swx_app.models": "swx_app/models",
        "swx_app.services": "swx_app/services",
        "swx_app.repositories": "swx_app/repositories",
        "swx_app.middleware": "swx_app/middleware",
        "swx_core.models": "swx_core/models",
        "swx_core.services": "swx_core/services",
        "swx_core.repositories": "swx_core/repositories",
        "swx_core.middleware": "swx_core/middleware",
        "swx_core.auth.admin": "swx_core/auth/admin",
        "swx_core.auth.user": "swx_core/auth/user",
        "swx_core.auth.core": "swx_core/auth/core",
    }

    for package, path in directories.items():
        modules = dynamic_import(path, package, recursive=True)
        print(f"Loaded {len(modules)} modules from {package}")


def load_middleware(app: FastAPI) -> None:
    """
    Dynamically loads middleware from `swx_core/middleware` and `swx_app/middleware`.

    Args:
        app (FastAPI): The FastAPI application instance.

    Middleware modules must define an `apply_middleware(app: FastAPI)` function to be applied.

    Example:
        ```
        def apply_middleware(app: FastAPI):
            app.add_middleware(SomeMiddleware)
        ```
    """
    # Ensure SessionMiddleware is applied first
    setup_session_middleware(app)

    middleware_modules = {
        **dynamic_import("swx_core/middleware", "swx_core.middleware", recursive=True),
        **dynamic_import("swx_app/middleware", "swx_app.middleware", recursive=True),
    }

    for module_name, module in middleware_modules.items():
        if hasattr(module, "apply_middleware"):
            try:
                module.apply_middleware(app)
                print(f"Applied middleware: {module_name}")
            except Exception as e:
                print(f"Failed to apply middleware {module_name}: {e}")
