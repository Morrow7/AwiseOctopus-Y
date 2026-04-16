import os
import importlib
import pkgutil

from .registry import registry

# 自动扫描当前目录并加载所有模块，触发 @registry.register 装饰器
package_dir = os.path.dirname(__file__)
for _, module_name, _ in pkgutil.iter_modules([package_dir]):
    if module_name != "registry":
        importlib.import_module(f".{module_name}", package=__name__)

__all__ = ["registry"]