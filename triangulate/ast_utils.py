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


class LineVisitor(ast.NodeVisitor):
  """Visit intra-statement lines in a Python script.

  Attributes:
    insertion_points:
  """

  def __init__(self):
    self.insertion_points = []

  def visit(self, node: ast.AST):
    if isinstance(
        node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)
    ):
      for i, child in enumerate(node.body):
        if isinstance(child, ast.Expr) and isinstance(
            child.value, ast.Constant
        ):
          continue  # Skip multiline string literals
        elif isinstance(child, (ast.Dict, ast.List)):
          continue  # Skip dictionary and list initializers
        elif hasattr(child, "lineno"):
          self.insertion_points.append((node, i))
    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
      return  # Skip multiline string literals
    self.generic_visit(node)


def get_insertion_points(tree: ast.AST):
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
  def visit_Name(self, node):  # pylint: disable=invalid-name
    self.identifiers.add(node.id)

  def visit_Call(self, node):  # pylint: disable=invalid-name
    for arg in node.args:
      self.visit(arg)


def extract_identifiers(expr):
  """Parse a Python expression and extract its identifiers."""
  root = ast.parse(expr)
  visitor = IdentifierExtractor()
  visitor.visit(root)
  return visitor.identifiers
