import ast
from typing import Any

from griffe import Extension, Inspector, Object, ObjectNode, Visitor


class MemberOrderFix(Extension):
    """Restore the original definition order of class and module members.

    Griffe uses ``inspect.getmembers``, which returns members sorted
    alphabetically. This extension re-sorts them to match the order they
    appear in the object's ``__dict__``, so the generated stubs reflect
    the order the author defined them in C++.
    """

    def on_members(
        self,
        *,
        node: ast.AST | ObjectNode,
        obj: Object,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        if not isinstance(node, ObjectNode) or not isinstance(agent, Inspector):
            return

        members = {}
        for k, v in node.obj.__dict__.items():
            if k in obj.members:
                members[k] = obj.members.pop(k)

        obj.members.update(members)
