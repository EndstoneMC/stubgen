import ast
import enum
import re
import typing
from typing import Any

from griffe import Attribute, ExprConstant, Extension, Inspector, ObjectNode, Visitor


class Pybind11NativeEnumSupport(Extension):
    """Normalize opaque ``pybind11::native_enum`` values into clean stub representations.

    Pybind11 native enums expose their values as opaque strings like
    ``<pkg.Mod.Color: 2>`` when introspected at runtime. This extension
    rewrites those values so the generated stubs are readable:

    - **Enum members** (value's type is a subclass of the parent enum):
      replaced by the underlying numeric value, e.g. ``2``.
    - **Exported entries** (created by ``export_values()``): replaced by the
      fully qualified enum name, e.g. ``pkg.Mod.Color``, and the inherited
      docstring is dropped since it duplicates the member's.
    """

    def on_attribute_instance(
        self,
        *,
        node: ast.AST | ObjectNode,
        attr: Attribute,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        if not isinstance(node, ObjectNode) or not isinstance(agent, Inspector):
            return

        pybind11_enum_pattern = re.compile(r"<(?P<enum>\w+(\.\w+)+): (?P<value>-?\d+)>")
        if isinstance(attr.value, str) and (match := pybind11_enum_pattern.match(attr.value)):
            value = node.obj
            tp = type(value)
            parent = node.parent.obj
            if isinstance(parent, type) and issubclass(tp, parent):
                # This is an entry of an enumeration
                attr.value = ExprConstant(f"{typing.cast(enum.Enum, value).value}")
            else:
                # this is an exported entry (i.e., pybind11::native_enum<Enum>::export_values())
                attr.value = match.group("enum")
                attr.docstring = None
