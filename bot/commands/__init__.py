import importlib
import pkgutil
from types import ModuleType
from inspect import getmembers, isfunction

from discord.ext.commands import Bot


def import_submodules(package_name) -> list[ModuleType]:
    """Import all direct submodules of a module"""
    package = importlib.import_module(package_name)
    modules = []
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        modules.append(importlib.import_module(full_name))

    return modules


def register_commands(bot: Bot):
    """Register all commands in submodules. Each submodule is assumed to have
    a single function definition. The module name is used as the name of the command.
    """
    modules = import_submodules("bot.commands")

    for module in modules:
        name = module.__name__.split('.')[-1]  # Get leaf module name
        (_, func), = getmembers(module, isfunction)  # Get the first function in the module (assumed to only be one)
        bot.command(name)(func)
