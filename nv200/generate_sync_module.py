"""
Script to generate synchronous wrapper modules for async Python modules.

It generates a sync version of the module suffixed with _sync.py,
wrapping all public functions (sync and async) and classes.

Usage:
    python generate_sync_module.py path/to/module.py
"""

import ast
import os
import sys
import textwrap
from pathlib import Path
from typing import List, Tuple


TEMPLATE_HEADER = '''"""
Auto-generated sync wrapper for `{original_module}`.

This module provides synchronous wrappers for async and sync functions and classes.
"""

import {original_module}
from syncwrap import run as _run
'''

FUNC_TEMPLATE_ASYNC = '''
def {name}({args}):
    """
    {docstring}
    """
    return _run({original_module}.{name}({call_args}))
'''

FUNC_TEMPLATE_SYNC = '''
def {name}({args}):
    """
    {docstring}
    """
    return {original_module}.{name}({call_args})
'''

CLASS_TEMPLATE = '''
class {name}:
    def __init__(self, *args, **kwargs):
        self._inner = {original_module}.{name}(*args, **kwargs)
'''

METHOD_TEMPLATE_ASYNC = '''
    def {name}(self, {args}):
        """
        {docstring}
        """
        return _run(self._inner.{name}({call_args}))
'''

METHOD_TEMPLATE_SYNC = '''
    def {name}(self, {args}):
        """
        {docstring}
        """
        return self._inner.{name}({call_args})
'''


def parse_args(func: ast.FunctionDef) -> Tuple[str, str]:
    """
    Returns (args_signature, call_signature) for a function.
    Skips 'self' for methods.
    """
    args = []
    call_args = []
    for arg in func.args.args:
        if arg.arg == "self":
            continue
        args.append(arg.arg)
        call_args.append(arg.arg)

    args_sig = ", ".join(args)
    call_sig = ", ".join(call_args)
    return args_sig, call_sig


def extract_functions(tree: ast.Module) -> List[ast.FunctionDef]:
    return [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    ]


def extract_classes(tree: ast.Module) -> List[ast.ClassDef]:
    classes = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            methods = [
                item for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_")
            ]
            if methods:
                classes.append((node, methods))
    return classes


def generate_sync_module(source_path: Path) -> None:
    """
    Generates a _sync.py file from a given async module.
    """
    with open(source_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code, filename=source_path.name)

    module_name = source_path.stem
    output_path = source_path.parent / f"{module_name}_sync.py"

    out: List[str] = [TEMPLATE_HEADER.format(original_module=module_name)]

    # All functions
    for func in extract_functions(tree):
        args_sig, call_sig = parse_args(func)
        doc = ast.get_docstring(func) or ""
        doc = textwrap.indent(textwrap.dedent(doc), "    ")
        if isinstance(func, ast.AsyncFunctionDef):
            out.append(FUNC_TEMPLATE_ASYNC.format(
                name=func.name,
                args=args_sig,
                call_args=call_sig,
                docstring=doc.strip(),
                original_module=module_name,
            ))
        else:
            out.append(FUNC_TEMPLATE_SYNC.format(
                name=func.name,
                args=args_sig,
                call_args=call_sig,
                docstring=doc.strip(),
                original_module=module_name,
            ))

    # Classes
    for cls, methods in extract_classes(tree):
        out.append(CLASS_TEMPLATE.format(name=cls.name, original_module=module_name))
        for method in methods:
            args_sig, call_sig = parse_args(method)
            doc = ast.get_docstring(method) or ""
            doc = textwrap.indent(textwrap.dedent(doc), "        ")
            if isinstance(method, ast.AsyncFunctionDef):
                out.append(METHOD_TEMPLATE_ASYNC.format(
                    name=method.name,
                    args=args_sig,
                    call_args=call_sig,
                    docstring=doc.strip()
                ))
            else:
                out.append(METHOD_TEMPLATE_SYNC.format(
                    name=method.name,
                    args=args_sig,
                    call_args=call_sig,
                    docstring=doc.strip()
                ))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print(f"✅ Generated sync module: {output_path}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python generate_sync_module.py path/to/module.py")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    generate_sync_module(path)


if __name__ == "__main__":
    main()
