import ast
from typing import Any

from griffe import Extension, Inspector, Module, ObjectNode, Visitor


class Pybind11SubmoduleSupport(Extension):
    """Force griffe to inspect pybind11 submodules that share the parent's binary.

    Griffe skips inspecting any submodule whose ``__file__`` is set, assuming
    it lives on disk and will be discovered by filesystem walking. In pybind11
    packages, however, every submodule's ``__file__`` points to the same
    ``.pyd`` / ``.so`` as the parent, so griffe never inspects them.

    This extension detects that situation and removes ``__file__`` from those
    submodules before inspection begins, causing griffe to treat them as
    in-memory modules and inspect them inline.
    """

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

        for child in node.children:
            if child.alias_target_path is None or not child.is_module:
                continue

            if child.alias_target_path != f"{agent.current.path}.{child.name}":
                continue

            if hasattr(child.obj, "__file__") and getattr(child.obj, "__file__") == getattr(node.obj, "__file__"):
                delattr(child.obj, "__file__")
