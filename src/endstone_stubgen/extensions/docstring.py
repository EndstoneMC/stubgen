import ast
import re
from typing import Any

from griffe import (
    Attribute,
    Class,
    Docstring,
    Expr,
    Extension,
    Function,
    Inspector,
    Module,
    ObjectNode,
    Parameter,
    ParameterKind,
    Parameters,
    Visitor,
    get_parameters,
    logger,
    parse_docstring_annotation,
    safe_get_annotation,
    safe_get_expression,
)


class Pybind11DocstringParser(Extension):
    """Parse pybind11 docstrings into typed function signatures and overloads.

    Pybind11 does not populate Python-level signatures; instead it encodes
    them as the first line of each function's docstring, e.g.::

        func(arg0: int, arg1: str) -> bool

    For overloaded functions the docstring lists multiple numbered
    signatures after an ``Overloaded function.`` header.

    This extension parses those lines with ``ast.compile``, constructs
    proper ``Parameters`` and return-type annotations, and — for overloads —
    splits them into separate ``Function`` objects. For properties, it
    extracts the return type from the getter's docstring signature.
    """

    def on_attribute_instance(
        self,
        *,
        node: ast.AST | ObjectNode,
        attr: Attribute,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        """Infer property return types from pybind11 getter docstrings."""
        if not isinstance(node, ObjectNode) or not isinstance(agent, Inspector):
            return

        fget = getattr(node.obj, "fget", None)
        if fget is None:
            return

        fget_node = ObjectNode(fget, node.name, node)
        docstring = agent._get_docstring(fget_node)
        if docstring is None:
            return

        top_signature_regex = re.compile(r"^\(.*\)\s*(->\s*(?P<returns>.+))?$")
        match = top_signature_regex.match(docstring.value)
        if match is None:
            return

        returns_str = match.group("returns")
        if returns_str is not None:
            attr.annotation = parse_docstring_annotation(returns_str, attr.docstring)

    def on_function_instance(
        self,
        *,
        node: ast.AST | ObjectNode,
        func: Function,
        agent: Visitor | Inspector,
        **kwargs: Any,
    ) -> None:
        """Extract parameter and return-type information from pybind11 docstrings.

        Parses the first line of the docstring as a signature. If the
        docstring indicates overloaded functions, splits them into separate
        ``Function`` overload objects with independent signatures.
        """
        if not isinstance(node, ObjectNode) or not isinstance(agent, Inspector):
            return

        if not func.docstring:
            return

        doc_lines = func.docstring.lines
        if len(doc_lines) == 0:
            return

        if isinstance(func.parent.get_member(func.name), Attribute):
            # Note: pybind *usually* does not include the function name in getter/setter signatures, e.g.:
            #   (arg0: demo._bindings.enum.ConsoleForegroundColor) -> int
            func_name = ""
        else:
            func_name = func.name

        top_signature_regex = re.compile(rf"^{func_name}\((?P<args>.*)\)\s*(->\s*(?P<returns>.+))?$")
        signature = doc_lines[0]
        if not top_signature_regex.match(signature):
            return

        func.parameters, func.returns = self.parse_signature(
            signature if func_name else func.name + signature, parent=func.parent
        )
        if func.parameters:
            if not func_name and func.parameters[0].name == "arg0":
                func.parameters[0].name = "self"
                func.parameters[0].annotation = None
            elif func_name and func.parameters[0].name == "self":
                func.parameters[0].annotation = None

        if len(doc_lines) < 2 or doc_lines[1] != "Overloaded function.":
            if len(doc_lines) > 1:
                func.docstring.value = "\n".join(doc_lines[1:]).lstrip()
            else:
                func.docstring = None

        else:
            overload_signature_regex = re.compile(
                rf"^(\s*(?P<overload_number>\d+).\s*)"
                rf"{func_name}\((?P<args>.*)\)\s*->\s*(?P<returns>.+)$"
            )

            doc_start = 0
            overloads = [func]

            for i in range(2, len(doc_lines)):
                match = overload_signature_regex.match(doc_lines[i])
                if match:
                    if match.group("overload_number") != f"{len(overloads)}":
                        continue
                    overloads[-1].docstring = Docstring("\n".join(doc_lines[doc_start:i]).lstrip())
                    doc_start = i + 1

                    overload = Function(name=func.name)
                    signature = f"{func_name}({match.group('args')}) -> {match.group('returns')}"

                    overload.parameters, overload.returns = self.parse_signature(signature, parent=func.parent)
                    if overload.parameters and overload.parameters[0].name == "self":
                        overload.parameters[0].annotation = None

                    overloads.append(overload)

            overloads[-1].docstring = Docstring("\n".join(doc_lines[doc_start:]).lstrip())

            func.overloads = overloads[1:]
            func.docstring = None

    def parse_signature(self, signature: str, *, parent: Module | Class) -> tuple[Parameters, str | Expr | None]:
        """Parse a pybind11 signature string into griffe Parameters and a return type.

        Compiles the signature as a Python ``def`` statement using ``ast``,
        then extracts parameter names, annotations, defaults, and the return
        annotation. Pybind11 enum literals (e.g., ``<Enum.VALUE: 1>``) are
        normalized before parsing.

        Args:
            signature: A pybind11 signature string like
                ``"func_name(arg0: int, arg1: str) -> bool"``.
            parent: The parent Module or Class, used to resolve annotations.

        Returns:
            A tuple of ``(parameters, return_annotation)``. On parse failure,
            falls back to ``(*args, **kwargs)`` with no return type.
        """
        try:
            pybind11_enum_pattern = re.compile(r"<(?P<enum>\w+(\.\w+)+): (?P<value>-?\d+)>")
            signature = pybind11_enum_pattern.sub(r"\g<enum>", signature)
            node = compile(
                f"def {signature}:...",
                mode="exec",
                filename="<>",
                flags=ast.PyCF_ONLY_AST,
                optimize=2,
            )
            node = node.body[0]
            parameters = Parameters(
                *[
                    Parameter(
                        name,
                        kind=kind,
                        annotation=safe_get_annotation(annotation, parent=parent, member=node.name),
                        default=None
                        if isinstance(default, str)
                        else safe_get_expression(default, parent=parent, parse_strings=False),
                    )
                    for name, annotation, kind, default in get_parameters(node.args)
                ],
            )
            returns = safe_get_annotation(node.returns, parent=parent, member=node.name)
            return parameters, returns

        except Exception as e:
            logger.warning(e, exc_info=True)
            parameters = Parameters(
                Parameter("args", kind=ParameterKind.var_positional),
                Parameter("kwargs", kind=ParameterKind.var_keyword),
            )

            return parameters, None
