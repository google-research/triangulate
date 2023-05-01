#!/usr/local/bin/python3
"""
This is executable pseudocode for an RL localiser.
 
Classes:
    State: A class to represent state.
    Agent: A base class for Agents
    Localiser(Agent): The localiser agent
    Environment: A class to represent the environment

Functions:
    TODO: not sure whether I'm supposed to list class methods here.
"""

# Standard Imports
import ast
import argparse
#import pdb
import os
import logging
import math
import pprint           # For manual debugging
#import random
import subprocess
import sys

# Third-party Imports
import coloredlogs
import numpy as np
import magic

# Local imports

# Module setup

log = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)     # For manual debugging

# Utility methods

# TODO:  Rewrite to use AST
def write_lines_to_file(descriptor, lines_with_offsets):
    """
    From a list of line and offset pairs, write each line to its offset to the given file descriptor

    Parameters:
        descriptor:  File descriptor to which the to write the lines to their paired offsets
        lines_with_offsets:  A list of lines paired with a target offset

    Returns: 
        None
    """
    for offset, line in lines_with_offsets:
        descriptor.seek(offset)
        descriptor.write(line)

# Get identifiers using Python's builtin AST.
def get_identifiers(expr):
    """
    Extract identifiers from a given expression.

    Parameters:
        expr: An expression

    Returns: 
        A list of the identifiers
    """
    try:
        compile(expr, '<string>', 'eval')
    except SyntaxError as e:
        err_template = "Error: %s is an invalid Python expression."
        log.error(err_template % expr)
        e.message = e.message + err_template % expr
        raise
    identifiers = set()
    node = ast.parse(expr, mode='eval')
    for subnode in ast.walk(node):
        if isinstance(subnode, ast.Name):
            identifiers.add(subnode.id)
    return identifiers

def sample_zipfian(num_samples, support_size = 10 ):
    """
    Generate a sample set from a Zipfian distribution over an integer interval

    Parameters:
        num_samples: The number of samples to return
        support_size:  The size of the support, i.e. the width of the interval

    Returns: 
        A sample set from a Zipfian
    """
    zipf_param = 1.5

    weights = np.array([1.0 / (i ** zipf_param)
                        for i in range(1, support_size+1)])
    weights /= np.sum(weights)

    return np.random.choice(np.arange(1, support_size+1), size=num_samples,
                            p=weights)

def sample_wo_replacement_uniform(num_samples, support):
    """
    Uniformly sample num_samples from [1, suppport].

    Parameters:
        num_samples: The number of samples to return
        support:  The upper bound of the sampled interval

    Returns: 
        A sample set from the uniform over the support
    """
    return np.random.choice(np.arange(1, len(support)+1), size=num_samples,
                            replace=False)

# Barebones RL

class State:
    """
    A class to represent state.

    Attributes:
        codeview : [str]
            code lines in current agent window
        ise : str
            illegal state expression
        focal_expression : str
            current expression 
        descriptor:
            file descriptor of program being debugged
        probes: [str x int]
            list of probes, which pair a query and an offset.

    Methods:
        get_illegal_state_expr_ids(self):
            Return identifiers in the illegal state expression
        def illegal_bindings(self):
            Return f-string for reporting illegal bindings
        def get_codeview(self):
            Return codeview 
        def to_string(self):
            Convert object into string representation
    """

    def __init__(self, descriptor, ise: str, focal_expr: str, probes = None):
        self.codeview = descriptor.readlines() # TODO: catch exceptions?
        self.ise = ise
        self.focal_expr = focal_expr
        self.descriptor = descriptor
        if probes is None:
            self.probes = []
        else:
            self.probes = probes

    def get_illegal_state_expr_ids(self):
        """
        Return identifiers in the illegal state expression

        Parameters:
            support:  The upper bound of the sampled interval

        Returns: 
            A sample set from the uniform over the support
        """
        return get_identifiers(self.ise)

    def illegal_bindings(self):
        """
        Return f-string for reporting illegal bindings

        Returns: 
            A sample set from the uniform over the support
        """
        idents = self.get_illegal_state_expr_ids()
        ident = idents.pop()
        bindings =  f"{ident} = " + "{" + f"{ident}" + "}"
        for ident in idents:
            bindings += f", {ident} = " + "{" + f"{ident}" + "}"
        return bindings

    def get_codeview(self):
        """
        Return codeview 
        """
        return self.codeview

    def to_string(self):
        """
        Convert object into string representation

        Returns: 
            Object contents serialised into a string.
        """
        print(self.descriptor, self.codeview)
        # TODO: implement.


class Agent:
    """
    A class to represent an agent.

    Attributes:
        total_reward : int
            the reward accumulator
        env : 
            the agent's environment

    Methods:
        __init__(self, env: Environment, reward: int = 0):
        pick_action(self, state: State, reward: int):
        add_probes(self, state: State, probes):
        to_string(self):
    """

    def __init__(self, env, reward: int = 0):
        """
        Agent constructor

        Attributes:
            total_reward: accumulated reward
            env: handle to the environment.

        Returns:
            An agent instance
        """
        self.env = env
        self.total_reward = reward

    def pick_action(self, state, reward: int) -> None:
        """
        Pick an action given the current state and reward

        Parameters:
            state: Current state
            reward:  Reward for last action and current state

        Returns: 
            None
        """
        print(f"abstract method, not sure it's needed; {state} {reward}",
              state, reward)

    def add_probes(self, state: State, probes):
        """ 
        Add probes to the codeview of the state

        Parameters:
            state: Current state
            probes:  list of probes, which pair queries and offsets

        Returns: 
            None
        """
        for offset, query in probes:
            state.codeview.insert(offset, query)
        state.descriptor.seek(0)
        state.descriptor.writelines(state.codeview)

    def to_string(self):
        """
        Convert object into string representation

        Returns: 
            Object contents serialised into a string.
        """
        print(self.total_reward) # want string, not newline to stderr


class Localiser(Agent):
    """
    A class to represent localiser agent.

    Attributes:
        codeview : [str]
            code lines in current agent window
        ise : str
            illegal state expression
        focal_expression : str
            current expression 
        descriptor:
            file descriptor of program being debugged
        probes: [str x int]
            list of probes, which pair a query and an offset.

    Methods:
        generate_probes(self, state) -> []:
        pick_action(self, state, reward: int) -> None:
    """


    def _generate_probes_random(self, state):
        #TODO: Handle imports needed by probe queries
        samples = sample_zipfian(1,5)
        codeview_length = len(state.codeview)
        offsets = sample_wo_replacement_uniform(samples[0],
                                                range(1, codeview_length))
        offsets.sort()
        offsets = [idx + v for idx, v in enumerate(offsets)]
        ise = f"Illegal state predicate: {state.ise} = " + "{eval(" + f"{state.ise}" + ")}; "
        isb = f"bindings: {state.illegal_bindings()}"
        query = 'f"' + ise + isb + '"'
        probes = []
        for offset in offsets:
            probes.append((offset, f"print({query})\n"))
        state.probes = probes       # Store probes
        return probes

    # TODO: Build AST, reverse its edges and walk the tree from focal
    #       expression to control expressions and defs
    # Ignore aliases for now.
    def _generate_probes_SE(self, state):
        print("Not implementated; {state}", state)
        sys.exit()

    # Answers two questions:  decides 1) where to query 2) what.
    # Returns list of probes
    def generate_probes(self, state) -> []:
        """ 
        Generate probes for the given state; to create each probe this
        function must decide whether to query what.

        Parameters: 
            state: current state

        Returns: 
            Object contents serialised into a string.
        """
        return self._generate_probes_random(state)

    def pick_action(self, state, reward: int) -> None:
        """
        Pick action in state

        Parameters:
            state: current state
            reward:  the reward for the previous state
        """
        # Todo:  add action selection
        #pp.pprint(f"state.codeview = {state.codeview}, reward = {reward},
        #          self.total_reward = {self.total_reward}")
        self.add_probes(state, self.generate_probes(state))
        self.total_reward += reward
        self.env.live = False


class Environment:
    """
    A class to represent the environment.

    Attributes:
        buggy_program_name: str
        buggy_program_output: str
        probe_output_filename: str
        steps: int
        max_steps: int
        descriptor: typeof(file descriptor)
        state: State

    Methods:
        __init__(self, args): Environment
        execute_subject(self) -> None:
        reward(self) -> int:
        terminate(self) -> None:
        update(self, action) -> None:
        to_string(self) -> str:
    """

    def __init__(self, args):
        """
        Construct an environment instance

        Parameters:
            args:  command line arguments

        Returns:
            An environment instance
        """
        self.buggy_program_name = args.buggy_program_name
        self.buggy_program_output = set()
        self.probe_output_filename = args.probe_output_filename
        self.steps = 0
        self.max_steps = args.max_steps
        if not args.burnin == 0:
            self.max_burnin = math.ceil(args.burnin*self.max_steps)
        else:
            self.max_burnin = args.max_steps

        file_type = magic.from_file(self.buggy_program_name, mime=True)
        if not file_type.startswith('text/x-script.python'):
            err_template = "Error: %s is not a Python script."
            log.error(err_template, self.buggy_program_name)
            raise ValueError(err_template, self.buggy_program_name)
        if not os.access(self.buggy_program_name, os.X_OK):
            err_template = "Error: %s is not executable."
            log.error(err_template, self.buggy_program_name)
            raise ValueError(err_template, self.buggy_program_name)
        try:
            self.descriptor = open(self.buggy_program_name, 'r+',
                                   encoding="utf-8")
        except IOError as e:
            log.error("Error: Unable to open file '%s'.",
                      self.buggy_program_name)
            raise e
        self.state = State(self.descriptor, args.illegal_state_expr,
                           args.bug_trap)

        try:
            cmd = ['./' + self.buggy_program_name]
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
        except subprocess.CalledProcessError as e:
            log.error("Error running command: %s", e)
            raise e
        except Exception as e:
            log.error("Error: %s", e)
            raise e
        self.buggy_program_output.add(result.stdout + result.stderr)

    def execute_subject(self) -> None:
        """
        Execute the program being debugged.
        """
        result = ""
        try:
            cmd = ['./' + self.buggy_program_name]
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdouterr = result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            log.error("Error running command: %s", e)
            raise e
        except Exception as e:
            log.error("Error: %s", e)
            raise e

        # This check --- for whether we've seen the output during burnin ---
        # is an instance of the coupon collector's problem.
        if self.steps > self.max_burnin and not stdouterr in self.buggy_program_output:
            err_template = "Error: probe insertion or "
            err_template += "execution changed program semantics."
            log.error(err_template)
            raise ValueError(err_template)

        self.buggy_program_output.add(stdouterr)
        # Create and return a new state instance
        # Probe's write their output to a fresh file

    def reward(self) -> int:
        """
        Return reward for current state

        Returns: 
            None
        """
         # TODO:
        return 1

    def terminate(self) -> None:
        """
        Terminate simulation

        Returns: 
            None
        """
        if self.steps >= self.max_steps:
            return True
        return False

    def update(self, action) -> None:
        """
        Update simulation given the selected action.

        Returns: 
            None
        """
        match action:
            case "Placeholder":
                pass
            case _:
                pass
        self.steps += 1
        self.execute_subject()

    def to_string(self) -> str:
        """
        Convert object into string representation

        Returns: 
            Object contents serialised into a string.
        """
        print("TODO")

def process_args():
    """
    Process command line arguments
    """

    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--buggy_program_name", required=True,
                        help="the name of a buggy file")
    parser.add_argument("-b", "--bug", required=True,
                        help="a bug-triggering input")
    parser.add_argument("-i", "--illegal_state_expr", required=True,
                        help="a predicate defining illegal state")
    parser.add_argument("-t", "--bug_trap", required=True,
                        help="program point at which the bug was observed")

    parser.add_argument("-v", help="log level")
    # During burnin, the program stores outputs for later use to checking
    # whether injecting/executing probes has changed program semantics.
    help_message = "percentage of max_steps to use as burnin steps "
    help_message += "to tolerate nondterministic buggy programs; "
    help_message += "zero (the default) disables burnin"
    parser.add_argument("-n", "--burnin", nargs='?', default=0, type=int,
                        help=help_message)
    parser.add_argument("-m", "--max_steps", nargs='?', default=10, type=int,
                        help="maximum simulation steps")
    parser.add_argument("-o", "--probe_output_filename", nargs='?',
                        const="__probeOutput.dmp", type=str,
                        help="maximum simulation steps")

    args = parser.parse_args()

    if not 0 <= args.burnin < 1:
        err_template = "Error: burnin period must fall into the interval [0,1)."
        log.error(err_template)
        raise ValueError(err_template)

    if args.__dict__.get("v", False):
        if 0 <= args.v < 6:
            log_levels = [ logging.NOTSET, logging.CRITICAL, logging.ERROR,
                logging.WARNING, logging.INFO, logging.DEBUG,
            ]
            coloredlogs.install(
                fmt="%(name)s [%(levelname)s]: %(message)s", level=log_levels[args.v]
            )
        logging.getLogger("localiser").setLevel(log_levels[args.v])

    if not args.buggy_program_name:
        args.buggy_program_name = input("Please enter the name of the buggy program: ")

    return args


def main():
    """
    program entry point
    """

    args = process_args()
    env = Environment(args)
    localiser = Localiser(env)

    while not env.terminate():
        env.update(localiser.pick_action(env.state, env.reward()))

if __name__ == "__main__":
    main()
