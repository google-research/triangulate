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

"""Main script."""

import argparse
import logging
import os

from triangulate import core

log = logging.getLogger(__name__)
Localiser = core.Localiser
Environment = core.Environment


def process_args():
  """Process command line arguments."""

  parser = argparse.ArgumentParser()

  parser.add_argument(
      "-p",
      "--buggy_program_name",
      required=True,
      help="the name of a buggy file",
  )
  parser.add_argument(
      "-b", "--bug", required=True, help="a bug-triggering input"
  )
  parser.add_argument(
      "-i",
      "--illegal_state_expr",
      required=True,
      help=(
          "A predicate defining illegal state; it is a fragment "
          "of the program's specification, which is almost never "
          "fully realised. Concretely, it will, for us, usually "
          "be the complement of an assertion."
      ),
  )
  parser.add_argument(
      "-t",
      "--bug_trap",
      required=True,
      help="program point at which the bug was observed",
  )

  parser.add_argument("-v", help="log level")
  # During burnin, the program stores outputs for later use to checking
  # whether injecting/executing probes has changed program semantics.
  help_message = (
      "Percentage of max_steps to use as burnin steps "
      "to tolerate nondeterministic buggy programs; "
      "zero (the default) disables burnin."
  )
  parser.add_argument(
      "-n", "--burnin", nargs="?", default=0, type=int, help=help_message
  )
  parser.add_argument(
      "-m",
      "--max_steps",
      nargs="?",
      default=10,
      type=int,
      help="maximum simulation steps",
  )
  parser.add_argument(
      "-o",
      "--probe_output_filename",
      nargs="?",
      const="__probeOutput.dmp",
      type=str,
      help="maximum simulation steps",
  )

  args = parser.parse_args()

  if not 0 <= args.burnin < 1:
    err_template = "Error: burnin period must fall into the interval [0,1)."
    log.error(err_template)
    raise ValueError(err_template)

  if args.__dict__.get("v", False):
    if 0 <= args.v < 6:
      log_levels = [
          logging.NOTSET,
          logging.CRITICAL,
          logging.ERROR,
          logging.WARNING,
          logging.INFO,
          logging.DEBUG,
      ]
      logging.getLogger("localiser").setLevel(log_levels[args.v])

  if not args.buggy_program_name:
    args.buggy_program_name = input(
        "Please enter the name of the buggy program: "
    )

  return args


def main():
  """Program entry point."""

  args = process_args()
  localiser = Localiser(Environment(args))

  while not Environment(args).terminate():
    Environment(args).update(
        localiser.pick_action(
            Environment(args).state, Environment(args).reward()
        )
    )

  try:
    os.remove(Environment(args).instrumented_program_name)
  except IOError as e:
    log.error(
        "Error: Unable to remove temp file '%s'.",
        Environment(args).instrumented_program_name,
    )
    raise e


if __name__ == "__main__":
  main()
