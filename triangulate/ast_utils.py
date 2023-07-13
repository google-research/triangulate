# Copyright 2023 The triangulate Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AST utilities."""

import ast


def is_assert_statement(statement: str) -> bool:
  try:
    parsed = ast.parse(statement.strip(" \n\t"))
    return isinstance(parsed.body[0], ast.Assert)
  except Exception:  # pylint: disable=broad-exception-caught
    return False


def extract_assert_expression(statement: str) -> str:
  parsed = ast.parse(statement.strip(" \n\t"))
  assert_node = parsed.body[0]
  expression = assert_node.test  # pytype: disable=attribute-error
  return ast.unparse(expression)


class LineVisitor(ast.NodeVisitor):
  """Visit intra-statement lines in a Python script.

  Attributes:
    insertion_points:
  """

  def __init__(self):
    self.insertion_points = []

  def visit(self, node: ast.AST) -> None:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
      return  # Skip multiline string literals
    elif isinstance(node, ast.Import):
      return  # Skip imports
    elif hasattr(node, "lineno"):
      self.insertion_points.append(node.lineno)
    if isinstance(
        node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)
    ):
      self.generic_visit(node)


def get_insertion_points(tree: ast.AST) -> list[int]:
  # Collect insertion points
  visitor = LineVisitor()
  visitor.visit(tree)
  insertion_points = visitor.insertion_points

  if not insertion_points:
    raise ValueError("No valid insertion points found.")

  return insertion_points


class IdentifierExtractor(ast.NodeVisitor):
  """This visitor extracts variables from an AST."""

  def __init__(self):
    self.identifiers = set()

  # This Google-violating function naming is required
  # to confirm with Python's builtin AST library's interface.
  def visit_Name(self, node: ast.Name) -> None:  # pylint: disable=invalid-name
    self.identifiers.add(node.id)

  def visit_Call(self, node: ast.Call) -> None:  # pylint: disable=invalid-name
    for arg in node.args:
      self.visit(arg)


def extract_identifiers(expr: str) -> set[str]:
  """Parse a Python expression and extract its identifiers."""
  root = ast.parse(expr)
  visitor = IdentifierExtractor()
  visitor.visit(root)
  return visitor.identifiers
