import importlib
import pkgutil
from inspect import getmembers, isfunction
from types import ModuleType

import discord


def import_submodules(package_name) -> list[ModuleType]:
    """Import all direct submodules of a module"""
    package = importlib.import_module(package_name)
    modules = []
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        modules.append(importlib.import_module(full_name))

    return modules


def register_event_handlers(client: discord.Client):
    """Register all event handlers in submodules. Each submodule is assumed to have
    a single async function definition.
    """
    modules = import_submodules("bot.events")

    for module in modules:
        (_, func), *_= getmembers(module, isfunction)  # Get the first function in the module (assumed to only be one)
        client.event(func)
