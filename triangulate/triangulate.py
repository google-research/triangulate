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
        errMsg = f"Error: {expr} is an invalid Python expression."
        log.error(errMsg)
        raise SyntaxError(errMsg)
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

    def __init__(self, fd, iSE, focalExpr, probes = []):
        self.codeview = fd.readlines() # TODO: catch exceptions?
        self.iSE = iSE
        self.focalExpr = focalExpr
        self.fd = fd
        self.probes = probes

    def getIllegalStateExprIds(self):
        return get_identifiers(self.iSE)

    def illegalBindings(self):
        # TODO: fix last binding ugliness
        bindings = ""
        for ident in self.getIllegalStateExprIds():
            bindings += f"{ident} = " + "{" + f"{ident}" + "}, "
        return bindings
 
    def getCodeView():
        return codeview

    def toString(self):
        print(self.file, self.lines)


class Agent:

    def __init__(self, env, reward = 0):
        self.totalReward = reward
        self.env = env

    def pickAction(self, state, reward):
        print("abstract method, not sure it's needed")

    def addProbes(self, state, probes):
        for offset, query in probes:
            state.codeview.insert(offset, query)
        state.fd.seek(0)
        state.fd.writelines(state.codeview)

    def toString(self):
        print(self.reward) # want string, not newline to stderr


class Localiser(Agent):

    def generateProbesRandom(self, state):
        #TODO: Handle inports needed by probe queries
        samples = sample_zipfian(1,5) 
        codeviewLength = len(state.codeview)
        offsets = sample_wo_replacement_uniform(samples[0], range(1, codeviewLength))
        offsets.sort()
        offsets = [idx + v for idx, v in enumerate(offsets)]
        iSE = state.iSE
        illegalStateExpr = f"Illegal state predicate: {iSE} = " + "{eval(" + f"{iSE}" + ")}"
        iSB = f"{state.illegalBindings()}"
        probes = []
        for offset in offsets:
            probes.append((offset, f"print({illegalStateExpr}; bindings: {iSB})\n"))
        state.probes = probes       # Store probes
        return probes
        
    # TODO: Build AST, reverse its edges and walk the tree from focal expression 
    #    to control expressions and defs
    # Ignore aliases for now.
    def generateProbesSE(self, state):
        raise Exception("Not implementated")

    # Answers two questions:  decides 1) where to query 2) what.
    # Returns list of probes
    def generateProbes(self, state):
        return self.generateProbesRandom(state)

    def pickAction(self, state, reward):
        # Todo:  add action selection; Google examples wire to gP.
        #pp.pprint(f"state.codeview = {state.codeview}, reward = {reward}, self.totalReward = {self.totalReward}")
        self.addProbes(state, self.generateProbes(state))
        self.totalReward += reward
        self.env.live = False

 
class Environment:

    def __init__(self, args):
        self.buggyProgramName = args.buggyProgramName
        self.buggyProgramOutput = set()
        self.probeOutputFilename = args.probeOutputFilename
        self.steps = 0
        self.maxSteps = args.maxSteps
        if not args.burnin == 0:
            self.maxBurnin = math.ceil(burnin*self.maxSteps) 
        else:
            self.maxBurnin = args.maxSteps

        file_type = magic.from_file(self.buggyProgramName, mime=True)
        if not file_type.startswith('text/x-script.python'):
            errMsg = f"Error: {self.buggyProgramName} is not a Python script."
            log.error(errMsg)
            raise Exception(errMsg)
        if not os.access(self.buggyProgramName, os.X_OK):
            errMsg = f"Error: {self.buggyProgramName} is not executable."
            log.error(errMsg)
            raise Exception(errMsg)
        try:
            self.fd = open(self.buggyProgramName, 'r+')
        except IOError:
            log.error(f"Error: Unable to open file '{self.buggyProgramName}'.")
            raise e
        self.state = State(self.fd, args.illegalStateExpr, args.bugTrap)

        try:
            cmd = ['./' + self.buggyProgramName] 
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

    def executeSubject(self):
        result = ""
        try:
            cmd = ['./' + self.buggyProgramName] 
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
            errMsg = f"Error: probe insertion or execution changed program semantics."
            log.error(errMsg)
            raise Exception(errMsg)

        self.buggyProgramOutput.add(stdouterr)
        # Create and return a new state instance
        # Probe's write their output to a fresh file

    def reward(self):
        # TODO: 
        return 1

    def terminate(self):
        if (self.steps >= self.maxSteps):
            return True
        return False

    def update(self, action):
        self.steps += 1
        self.executeSubject()
    
    def toString(self):
        print("TODO")

def processArgs():

    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--buggyProgramName", required=True, help="the name of a buggy file")
    parser.add_argument("-b", "--bug", required=True, help="a bug-triggering input") 
    parser.add_argument("-i", "--illegalStateExpr", required=True, help="a predicate defining illegal state") 
    parser.add_argument("-t", "--bugTrap", required=True, help="program point at which the bug was observed") 

    parser.add_argument("-v", help="log level") 
    # During burnin, the program stores outputs for later use to checking whether 
    # injecting/executing probes has changed program semantics.
    parser.add_argument("-n", "--burnin", nargs='?', default=0, type=int, help="percentage of maxSteps to use as burnin steps to tolerate nondterministic buggy programs; zero (the default) disables burnin") 
    parser.add_argument("-m", "--maxSteps", nargs='?', default=10, type=int, help="maximum simulation steps") 
    parser.add_argument("-o", "--probeOutputFilename", nargs='?', const="__probeOutput.dmp", type=str, help="maximum simulation steps") 

    args = parser.parse_args()

    if not 0 <= args.burnin < 1:
        errMsg = "Error: burnin period must fall into the interval [0,1)."
        log.error(errMsg)
        raise Exception(errMsg)
 
    if args.__dict__.get("v", False):
        if 0 <= args.v < 6:
            log_levels = [ logging.NOTSET, logging.CRITICAL, logging.ERROR, 
                logging.WARNING, logging.INFO, logging.DEBUG,
            ]
            coloredlogs.install(
                fmt="%(name)s [%(levelname)s]: %(message)s", level=log_levels[args.v]
            )
        logging.getLogger("localiser").setLevel(log_levels[args.v])

    if not args.buggyProgramName:
        args.buggyProgramName = input("Please enter the name of the buggy program: ")

    return args


def main():

    args = processArgs()
    env = Environment(args)
    localiser = Localiser(env)

    while(not env.terminate()):
        env.update(localiser.pickAction(env.state, env.reward()))

if __name__ == "__main__":
    main()
