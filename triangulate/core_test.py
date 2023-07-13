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

"""Tests for core."""

import os

from absl.testing import absltest
from absl.testing import parameterized
from triangulate import core

TESTDATA_DIRECTORY = os.path.join(
    absltest.get_default_test_srcdir(),
    "triangulate/testdata",
)
TEST_PROGRAM_PATH = os.path.join(TESTDATA_DIRECTORY, "quoter.py")
TEST_PROGRAM_ASSERT_LINE_NUMBER = 40


class EnvironmentTest(parameterized.TestCase):

  @parameterized.named_parameters(
      dict(
          testcase_name='test_a',
          buggy_program_name=TEST_PROGRAM_PATH,
          illegal_state_expr='1 == 1',
          bug_triggering_input='42',
          bug_trap=TEST_PROGRAM_ASSERT_LINE_NUMBER,
          action='<placeholder>',
          expected_output='''\
Today's inspirational quote:
"Believe you can and you're halfway there." - Theodore Roosevelt
''',
      ),
      dict(
          testcase_name='test_b',
          buggy_program_name=TEST_PROGRAM_PATH,
          illegal_state_expr='2 == 2',
          bug_triggering_input='42',
          bug_trap=TEST_PROGRAM_ASSERT_LINE_NUMBER,
          action='<placeholder>',
          expected_output='''\
Today's inspirational quote:
"Believe you can and you're halfway there." - Theodore Roosevelt
''',
      ),
  )
  def test_execute_and_update(
      self,
      buggy_program_name: str,
      illegal_state_expr: str,
      bug_triggering_input: str,
      bug_trap: int,
      action: str,
      expected_output: str,
      burnin: int = 100,
      max_steps: int = 100,
      probe_output_filename: str = '',
  ):
    env = core.Environment(
        buggy_program_name=buggy_program_name,
        illegal_state_expr=illegal_state_expr,
        bug_triggering_input=bug_triggering_input,
        bug_trap=bug_trap,
        burnin=burnin,
        max_steps=max_steps,
        probe_output_filename=probe_output_filename,
    )
    # TODO(etbarr): Test `execute_subject` and `update` methods.
    output = env.execute_subject()
    print(output)
    env.update(action=action)
    self.assertEqual(output, expected_output)


class LocaliserTest(parameterized.TestCase):

  @parameterized.named_parameters(
      dict(
          testcase_name='test_a',
          buggy_program_name=TEST_PROGRAM_PATH,
          illegal_state_expr='1 == 1',
          bug_triggering_input='5',
          bug_trap=TEST_PROGRAM_ASSERT_LINE_NUMBER,
      ),
  )
  def test_generate_probes_random(
      self,
      buggy_program_name: str,
      illegal_state_expr: str,
      bug_triggering_input: str,
      bug_trap: int,
      burnin: int = 100,
      max_steps: int = 100,
      probe_output_filename: str = 'probe_output.txt',
  ):
    test_filepath = os.path.join(TESTDATA_DIRECTORY, buggy_program_name)
    env = core.Environment(
        buggy_program_name=test_filepath,
        illegal_state_expr=illegal_state_expr,
        bug_triggering_input=bug_triggering_input,
        bug_trap=bug_trap,
        burnin=burnin,
        max_steps=max_steps,
        probe_output_filename=probe_output_filename,
    )
    localiser = core.Localiser(env)
    localiser._generate_probes_random(env.state)


if __name__ == "__main__":
  absltest.main()
