#!/usr/local/bin/python3

import ast
import argparse
import coloredlogs
import pdb
import os
import logging
import magic
import math
import numpy as np
import pprint           # For manual debugging
import random
import subprocess
import sys

# Module setup

log = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)     # For manual debugging

# Utility methods

# TODO:  Rewrite to use AST
def write_lines_to_file(fd, lines_with_offsets):
    for offset, line in lines_with_offsets:
        fd.seek(offset)
        fd.write(line)

# Get identifiers using Python's builtin AST.
def get_identifiers(expr):
    try:
        compile(expr, '<string>', 'eval')
    except SyntaxError as e:
        err_msg = f"Error: {expr} is an invalid Python expression."
        log.error(err_msg)
        raise SyntaxError(err_msg)
    identifiers = set()
    node = ast.parse(expr, mode='eval')
    for subnode in ast.walk(node):
        if isinstance(subnode, ast.Name):
            identifiers.add(subnode.id)
    return identifiers

def sample_zipfian(num_samples, support_size = 10 ):
    zipf_param = 1.5

    weights = np.array([1.0 / (i ** zipf_param) for i in range(1, support_size+1)])
    weights /= np.sum(weights)

    return np.random.choice(np.arange(1, support_size+1), size=num_samples, p=weights)

def sample_wo_replacement_uniform(num_samples, support):
    return np.random.choice(np.arange(1, len(support)+1), size=num_samples, replace=False)

# Barebones RL

class State:

    def __init__(self, fd, ise, focal_expr, probes = []):
        self.codeview = fd.readlines() # TODO: catch exceptions?
        self.ise = ise
        self.focal_expr = focal_expr
        self.fd = fd
        self.probes = probes

    def get_illegal_state_expr_ids(self):
        return get_identifiers(self.ise)

    def illegal_bindings(self):
        idents = self.get_illegal_state_expr_ids()
        ident = idents.pop()
        bindings =  f"{ident} = " + "{" + f"{ident}" + "}"
        for ident in idents:
            bindings += f", {ident} = " + "{" + f"{ident}" + "}"
        return bindings

    def get_codeview(self):
        return codeview

    def to_string(self):
        print(self.file, self.lines)


class Agent:

    def __init__(self, env, reward = 0):
        self.totalReward = reward
        self.env = env

    def pick_action(self, state, reward):
        print("abstract method, not sure it's needed")

    def add_probes(self, state, probes):
        for offset, query in probes:
            state.codeview.insert(offset, query)
        state.fd.seek(0)
        state.fd.writelines(state.codeview)

    def to_string(self):
        print(self.reward) # want string, not newline to stderr


class Localiser(Agent):

    def _generate_probes_random(self, state):
        #TODO: Handle imports needed by probe queries
        samples = sample_zipfian(1,5)
        codeviewLength = len(state.codeview)
        offsets = sample_wo_replacement_uniform(samples[0], range(1, codeviewLength))
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

    # TODO: Build AST, reverse its edges and walk the tree from focal expression
    #    to control expressions and defs
    # Ignore aliases for now.
    def _generate_probes_SE(self, state):
        raise Exception("Not implementated")

    # Answers two questions:  decides 1) where to query 2) what.
    # Returns list of probes
    def generate_probes(self, state):
        return self._generate_probes_random(state)

    def pick_action(self, state, reward):
        # Todo:  add action selection; Google examples wire to gP.
        #pp.pprint(f"state.codeview = {state.codeview}, reward = {reward}, self.totalReward = {self.totalReward}")
        self.add_probes(state, self.generate_probes(state))
        self.totalReward += reward
        self.env.live = False


class Environment:

    def __init__(self, args):
        self.buggy_program_name = args.buggy_program_name
        self.buggyProgramOutput = set()
        self.probe_output_filename = args.probe_output_filename
        self.steps = 0
        self.max_steps = args.max_steps
        if not args.burnin == 0:
            self.maxBurnin = math.ceil(burnin*self.max_steps)
        else:
            self.maxBurnin = args.max_steps

        file_type = magic.from_file(self.buggy_program_name, mime=True)
        if not file_type.startswith('text/x-script.python'):
            err_msg = f"Error: {self.buggy_program_name} is not a Python script."
            log.error(err_msg)
            raise Exception(err_msg)
        if not os.access(self.buggy_program_name, os.X_OK):
            err_msg = f"Error: {self.buggy_program_name} is not executable."
            log.error(err_msg)
            raise Exception(err_msg)
        try:
            self.fd = open(self.buggy_program_name, 'r+')
        except IOError:
            log.error(f"Error: Unable to open file '{self.buggy_program_name}'.")
            raise e
        self.state = State(self.fd, args.illegal_state_expr, args.bug_trap)

        try:
            cmd = ['./' + self.buggy_program_name]
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
        except subprocess.CalledProcessError as e:
            log.error(f"Error running command: {e}")
            raise e
        except Exception as e:
            log.error(f"Error: {e}")
            raise e
        self.buggyProgramOutput.add(result.stdout + result.stderr)

    def execute_subject(self):
        result = ""
        try:
            cmd = ['./' + self.buggy_program_name]
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdouterr = result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            log.error(f"Error running command: {e}")
            raise e
        except Exception as e:
            log.error(f"Error: {e}")
            raise e

        # This check --- for whether we've seen the output during burnin --- is an instance
        # of the coupon collector's problem.
        if(self.steps > self.maxBurnin and not stdouterr in self.buggyProgramOutput):
            err_msg = f"Error: probe insertion or execution changed program semantics."
            log.error(err_msg)
            raise Exception(err_msg)

        self.buggyProgramOutput.add(stdouterr)
        # Create and return a new state instance
        # Probe's write their output to a fresh file

    def reward(self):
        # TODO:
        return 1

    def terminate(self):
        if (self.steps >= self.max_steps):
            return True
        return False

    def update(self, action):
        self.steps += 1
        self.execute_subject()

    def to_string(self):
        print("TODO")

def process_args():

    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--buggy_program_name", required=True, help="the name of a buggy file")
    parser.add_argument("-b", "--bug", required=True, help="a bug-triggering input")
    parser.add_argument("-i", "--illegal_state_expr", required=True, help="a predicate defining illegal state")
    parser.add_argument("-t", "--bug_trap", required=True, help="program point at which the bug was observed")

    parser.add_argument("-v", help="log level")
    # During burnin, the program stores outputs for later use to checking whether
    # injecting/executing probes has changed program semantics.
    parser.add_argument("-n", "--burnin", nargs='?', default=0, type=int, help="percentage of max_steps to use as burnin steps to tolerate nondterministic buggy programs; zero (the default) disables burnin")
    parser.add_argument("-m", "--max_steps", nargs='?', default=10, type=int, help="maximum simulation steps")
    parser.add_argument("-o", "--probe_output_filename", nargs='?', const="__probeOutput.dmp", type=str, help="maximum simulation steps")

    args = parser.parse_args()

    if not 0 <= args.burnin < 1:
        err_msg = "Error: burnin period must fall into the interval [0,1)."
        log.error(err_msg)
        raise Exception(err_msg)

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

    args = process_args()
    env = Environment(args)
    localiser = Localiser(env)

    while(not env.terminate()):
        env.update(localiser.pick_action(env.state, env.reward()))

if __name__ == "__main__":
    main()
