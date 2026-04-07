import ast
from typing import Any

from griffe import Attribute, Extension, Function, Inspector, ObjectNode, Visitor


class Pybind11PropertySupport(Extension):
    """Create griffe setter/deleter nodes for pybind11 properties.

    Griffe only records the getter side of pybind11 properties. When a
    property also exposes ``fset`` or ``fdel`` callables, this extension
    wraps each in a ``Function`` node, attaches it to the ``Attribute`` as
    ``attr.setter`` / ``attr.deleter``, and fires the standard
    ``on_function_instance`` hooks so downstream extensions (e.g., the
    docstring parser) can process their signatures too.

    Properties that gain a setter are labeled *writable*; those that gain a
    deleter are labeled *deletable*.
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

        if "property" not in attr.labels:
            return

        if fset := getattr(node.obj, "fset", None):
            fset_node = ObjectNode(fset, node.name, node)
            setter = Function(
                name=node.name,
                docstring=agent._get_docstring(fset_node),
                parent=agent.current,
            )
            attr.setter = setter
            attr.labels.add("writable")
            agent.extensions.call("on_instance", node=fset_node, obj=setter, agent=agent)
            agent.extensions.call("on_function_instance", node=fset_node, func=setter, agent=agent)

        if fdel := getattr(node.obj, "fdel", None):
            fdel_node = ObjectNode(fdel, node.name, node)
            deleter = Function(
                name=node.name,
                docstring=agent._get_docstring(fdel_node),
                parent=agent.current,
            )
            attr.deleter = deleter
            attr.labels.add("deletable")
            agent.extensions.call("on_instance", node=fdel_node, obj=deleter, agent=agent)
            agent.extensions.call("on_function_instance", node=fdel_node, func=deleter, agent=agent)
