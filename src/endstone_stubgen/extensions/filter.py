import ast
from typing import Any

from griffe import Attribute, Class, Extension, Inspector, Object, ObjectNode, Visitor


class Pybind11InternalsFilter(Extension):
    """Strip pybind11 implementation details that should not appear in stubs.

    Pybind11 modules contain many internal members (``__module__``,
    ``__dict__``, ``_pybind11_conduit_v1_``, etc.) that are not part of
    the public API. This extension removes them, along with:

    - The ``pybind11_builtins.pybind11_object`` base class from class
      hierarchies (an implementation detail, not a real base).
    - Attribute docstrings that are just inherited from the value's type
      (e.g., ``int``'s docstring on an ``int``-typed attribute).
    - The default ``__init__`` when its docstring is identical to
      ``object.__init__``'s, indicating pybind11 did not define a
      custom constructor.
    """

    def on_members(
        self,
        *,
        node: ast.AST | ObjectNode,
        obj: Object,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        for member in {
            "__annotations__",
            "__builtins__",
            "__cached__",
            "__class__",
            "__dict__",
            "__doc__",
            "__file__",
            "__firstlineno__",
            "__format__",
            "__loader__",
            "__module__",
            "__name__",
            "__package__",
            "__path__",
            "_pybind11_conduit_v1_",
            "__qualname__",
            "__spec__",
            "__static_attributes__",
            "__weakref__",
        }:
            obj.members.pop(member, None)

    def on_attribute_instance(
        self,
        *,
        node: ast.AST | ObjectNode,
        attr: Attribute,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        """Strip docstrings that are inherited from the attribute's type rather than defined by the user."""
        if not isinstance(node, ObjectNode) or not isinstance(agent, Inspector):
            return

        if attr.docstring is not None and attr.docstring.value == type(node.obj).__doc__:
            attr.docstring = None

    def on_class_instance(
        self,
        *,
        node: ast.AST | ObjectNode,
        cls: Class,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        cls.bases = [base for base in cls.bases if base != "pybind11_builtins.pybind11_object"]

    def on_class_members(
        self,
        *,
        node: ast.AST | ObjectNode,
        cls: Class,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        """Remove ``__init__`` if its docstring matches the default ``object.__init__``."""
        if "__init__" in cls.members:
            func = cls.members["__init__"]
            if func.docstring is not None and func.docstring.value == object.__init__.__doc__:
                cls.members.pop("__init__")
