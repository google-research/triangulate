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

"""Tests for third_party.py.triangulate."""

import ast
import os

from absl.testing import absltest
from triangulate import ast_utils

TESTDATA_DIRECTORY = os.path.join(
    absltest.get_default_test_srcdir(),
    "triangulate/testdata",
)
TEST_PROGRAM_PATH = os.path.join(TESTDATA_DIRECTORY, "quoter.py")


class ASTTest(absltest.TestCase):

  def test_get_insertion_points(self):
    with open(TEST_PROGRAM_PATH, "r") as f:
      source = f.read()
    tree = ast.parse(source)
    insertion_points = ast_utils.get_insertion_points(tree)
    print(insertion_points)  # Debugging, not sure of the current value
    # TODO(etbarr): Verify whether `insertion_points` is correct.
    self.assertLen(insertion_points, 7)

  def test_extract_identifiers(self):
    test_expr = "x + y * foo(z,c)"
    test_expr_fv = set(["c", "x", "y", "z"])
    fv = ast_utils.extract_identifiers(test_expr)
    self.assertEqual(test_expr_fv, set(fv))


if __name__ == "__main__":
  absltest.main()
