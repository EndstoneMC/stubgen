import ast
import builtins
from collections import defaultdict
from typing import Any

from griffe import (
    Alias,
    Attribute,
    Class,
    Expr,
    ExprAttribute,
    ExprName,
    Extension,
    Function,
    Inspector,
    Module,
    ObjectNode,
    Visitor,
    logger,
)


class Pybind11ImportFix(Extension):
    """Collect and emit ``import`` statements needed by generated stubs.

    Pybind11 modules have no source-level imports; type annotations
    reference fully qualified names like ``pkg.sub.MyClass``. This
    extension walks every annotation in the module tree, determines
    whether each reference is internal (same top-level package) or
    external, registers a short alias, and builds the sorted ``import``
    / ``from … import …`` block that the Jinja template writes at the
    top of each ``.pyi`` file.
    """

    def __init__(self):
        self.module: Module | None = None
        self.current: Module | Class | None = None

    def on_module_instance(
        self,
        *,
        node: ast.AST | ObjectNode,
        mod: Module,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        if not isinstance(node, ObjectNode) or not isinstance(agent, Inspector):
            return

        if self.module is not None:
            return

        self.module = mod

    def on_module_members(
        self,
        *,
        node: ast.AST | ObjectNode,
        mod: Module,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        if self.module is not mod:
            return

        if not isinstance(node, ObjectNode) or not isinstance(agent, Inspector):
            return

        self.current = mod
        self.handle_module(mod)
        self.module = None

    def handle_module(self, mod: Module) -> None:
        """Walk all members of a module, resolve imports, and sort the import list.

        Args:
            mod: The module whose members and imports to process.
        """
        self.current = mod
        for keys in list(mod.members.keys()):
            child = mod.members[keys]
            if isinstance(child, Alias):
                continue

            if cb := getattr(self, f"handle_{child.kind.name.lower()}", None):
                cb(child)

        import_list = []
        importfrom_list = defaultdict(list)
        for as_name, name in mod.imports.items():
            if as_name == name:
                import_list.append(name)
            else:
                module, obj = name.rsplit(".", maxsplit=1)
                importfrom_list[module].append(obj)

        imports: dict[str, str] = {}
        for name in sorted(import_list):
            imports[name] = name

        for module in sorted(importfrom_list.keys()):
            objects = importfrom_list[module]
            for obj in sorted(objects):
                imports[obj] = f"{module}.{obj}"

        mod.imports = imports

    def handle_class(self, cls: Class) -> None:
        """Resolve imports for a class's bases and all of its members.

        Args:
            cls: The class to process.
        """
        self.current = cls

        cls.bases = [self._add_import(base) for base in cls.bases]
        for keys in list(cls.members.keys()):
            child = cls.members[keys]
            if isinstance(child, Alias):
                continue

            if cb := getattr(self, f"handle_{child.kind.name.lower()}", None):
                cb(child)

        self.current = self.current.parent

    def handle_function(self, func: Function) -> None:
        """Resolve imports for a function's return type, parameter annotations, and overloads.

        Args:
            func: The function to process.
        """
        func.returns = self._add_import(func.returns)
        for parameter in func.parameters:
            if parameter.annotation is not None:
                parameter.annotation = self._add_import(parameter.annotation)

        if func.overloads:
            self._add_import("typing.overload")
            for overload in func.overloads:
                self.handle_function(overload)

    def handle_attribute(self, attr: Attribute) -> None:
        """Resolve imports for an attribute's annotation and any setter/deleter.

        Args:
            attr: The attribute to process.
        """
        attr.annotation = self._add_import(attr.annotation)

        if attr.setter:
            self.handle_function(attr.setter)

        if attr.deleter:
            self.handle_function(attr.deleter)

    def _add_import(self, name: Expr | str | None) -> Expr | str | None:
        """Register an import for a type reference and return its stub-file name.

        Recursively processes compound expressions (e.g., generics).
        For simple names, distinguishes between internal references (within
        the top-level module being stubbed) and external references, then
        adds the appropriate import entry and alias to the module.

        Args:
            name: The type expression or dotted name to resolve. ``None``
                and empty values are returned unchanged.

        Returns:
            The name as it should appear in the stub file (may be shortened
            for internal references).
        """
        if not name:
            return name

        if isinstance(name, Expr):
            if isinstance(name, ExprAttribute) or isinstance(name, ExprName):
                name = name.path
            else:
                result = "".join([self._add_import(e) if isinstance(e, Expr) else e for e in name])
                return result

        if hasattr(builtins, name):
            return name

        if name.startswith(self.module.path + "."):
            # internal import
            target = self.module.get_member(name[len(self.module.path) + 1 :])

            if self.current.is_class and target.parent.path == self.current.path:
                return target.name

            if target.module.path == self.current.module.path:
                return target.path[len(self.current.module.path) + 1 :]

            alias_path = name
            alias_name = name.rsplit(".", 1)[-1]
            final_name = alias_name

        else:
            # external import
            alias_path = name.split(".", 1)[0]
            alias_name = alias_path.split(".", 1)[0]
            final_name = name

        if alias_name in self.current.module.imports:
            if self.current.module.imports[alias_name] != alias_path:
                logger.warning(
                    f"Alias {alias_name} already exists with different path: {self.current.module.imports[alias_name]}"
                )

            return final_name

        if alias_name in self.current.module.members:
            logger.warning(f"Member {alias_name} already exists in {self.current.module.path}")
            return final_name

        self.current.module.imports[alias_name] = alias_path
        alias = Alias(alias_name, alias_path)
        self.current.module.set_member(alias_name, alias)

        return final_name


class Pybind11ExportFix(Extension):
    """Generate ``__all__`` for pybind11 modules that lack one.

    Pybind11 modules rarely define ``__all__``. Without it the stub file
    would have no explicit export list, which breaks ``from pkg import *``
    semantics and some linter checks. This extension populates ``__all__``
    with every non-alias member name, sorted alphabetically.
    """

    def on_module_members(
        self,
        *,
        node: ast.AST | ObjectNode,
        mod: Module,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        if not isinstance(node, ObjectNode) or not isinstance(agent, Inspector):
            return

        if mod.exports is not None:
            return

        mod.exports = sorted([child.name for child in mod.members.values() if not isinstance(child, Alias)])
