#!/usr/bin/env python3

GPL = """
AF solver.
Copyright (C) 2017-2019  Mario Alviano (mario@alviano.net)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

VERSION = "0.7"

import argparse
from collections import OrderedDict
import fileinput
import re
import os
#import subprocess
import sys
#import tempfile

class OrderedSet:
    def __init__(self): self.data = OrderedDict()
    def add(self, value): self.data[value] = None
    def __iter__(self):
        for key in self.data: yield key

# the arguments of the AF
arg = [None]

# dictionary to store the integer representation for each argument
argToIdx = {}

# the attack relation of the AF, stored in the form of the sets a⁺ and a⁻ for every argument a in AF
att = OrderedDict()
attR = OrderedDict()


def x(name):
    if name not in x.name2idx:
        x.name2idx[name] = len(arg) + len(x.names)
        x.names.append(name)
        #print(x.name2idx[name],name)
    return x.name2idx[name]
x.name2idx = {}
x.names = []

def resolve(b): return b if isinstance(b, int) else argToIdx[b]
def attacked(b): return x(('attacked', resolve(b)))
def inRange(b): return x(('inRange', resolve(b)))
def attack(a, b): return x(('attack', resolve(a), resolve(b)))
def attackAndAttacker(a, b): return x(('attackAndAttacker', resolve(a), resolve(b)))
def defended(a, b): return x(('defended', resolve(a), resolve(b)))

class AF:
    def __init__(self):
        # the arguments of the AF
        self.arg = [None]
        # the attack relation of the AF, stored in the form of the sets a⁺ and a⁻ for every argument a in AF
        self.attacḱed = OrderedDict()
        self.attacḱers = OrderedDict()
        # dictionary to store the integer representation for each argument
        self.argToIdx = {}

sol = None

def printModel(m):
    print('[', end='')
    print(','.join(m), end='')
    print(']', end='')
    sys.stdout.flush()

def printAll(solver, end='\n'):
    while True:
        line = solver.stdout.readline()
        if not line: break
        print(line.decode().rstrip(), end=end)

def DS(solver):
    while True:
        line = solver.stdout.readline()
        if not line: break
        print(line.decode().strip())

def DC(solver):
    while True:
        line = solver.stdout.readline()
        if not line: break
        print(line.decode().strip())

def SE(solver, end='\n'):
    while True:
        line = solver.stdout.readline()
        if not line: break
        line = line.decode().strip().split()
        if line[0] == 'UNSATISFIABLE': print('NO', end=''); return
        printModel(line)
    print(end=end)

def EE(solver, end='\n'):
    print('[', end='')
    count = 0
    while True:
        line = solver.stdout.readline()
        if not line: break
        line = line.decode().strip().split()
        if line[0] == 'v':
            if count != 0: print(',', end='')
            count += 1
            printModel(line[1:])
    print(']', end=end)

def DC_via_SE(solver, a):
    while True:
        line = solver.stdout.readline()
        if not line: break
        line = line.decode().strip().split()
        if line[0] == 'v':
            if a in line[1:]: print('YES')
            else: print('NO')

def DC_via_EE(solver, a):
    while True:
        line = solver.stdout.readline()
        if not line: break
        line = line.decode().strip().split()
        if line[0] == 'v':
            if a in line[1:]:
                print('YES')
                return
    print('NO')

def DS_via_EE(solver, a):
    while True:
        line = solver.stdout.readline()
        if not line: break
        line = line.decode().strip().split()
        if line[0] == 'v':
            if a not in line[1:]:
                print('NO')
                return
    print('YES')

# start of file
def preamble(stream, soft=[]):
    stream.write(('p cnf %i %i\n' %(len(args), len(clauses))).encode())

# end of line symbol
def close(stream):
    stream.write('0\n'.encode())

def CO(stream):
    preamble(stream)
    #conflictFree(stream)
    #buildAttacked(stream)
    #admissible(stream)
    #complete(stream)
    #buildAttackAndAttacked(stream)
    #buildDefended(stream)
    #buildAssumptions(stream)

def computeAttackedBy(union):
    attacked = set()
    for a in arg[1:]:
        # we are only interested to arguments in the union
        if a not in union:
            attacked.add(a)
            continue

        if a not in attR: continue
        for b in attR[a]:
            if b not in union: continue
            attacked.add(a)
            break
    return attacked


problemFunctions = {
    #"DC-CO" : DC_CO, "DS-CO" : DS_CO, "SE-CO" : SE_CO, "CE-CO" : CE_CO,
}


def parseArguments():
    global VERSION
    global GPL
    parser = argparse.ArgumentParser(description=GPL.split("\n")[1], epilog="Copyright (C) 2017  Mario Alviano (mario@alviano.net)")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION, help='print version number')
    parser.add_argument('--formats', action='store_true', help='print supported formats and exit')
    parser.add_argument('--problems', action='store_true', help='print supported computational problems and exit')
    parser.add_argument('-p', metavar='<task>', type=str, help='')
    parser.add_argument('-f', metavar='<file>', type=str, help='')
    #parser.add_argument('-m', metavar='<file>', type=str, help='')
    parser.add_argument('-fo', metavar='<fileformat>', type=str, help='')
    parser.add_argument('-a', metavar='<additional_parameter>', type=str, help='')
    parser.add_argument('--circ', metavar='<file>', type=str, help='path to circumscriptino (default is circumscriptino-static in the script directory)')
    parser.add_argument('--print-circ', action='store_true', help='print numeric format for circumscriptino and exit')
    args = parser.parse_args()
    if args.formats:
        print('[%s]' % ','.join(sorted(parseFunctions.keys())))
        sys.exit()
    if args.problems:
        print('[%s]' % ','.join(sorted(problemFunctions.keys())))
        sys.exit()
    if not args.circ: args.circ = os.path.dirname(os.path.realpath(__file__)) + '/circumscriptino-static'
    return args

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(sys.argv[0], VERSION)
        print("Mario Alviano")
        sys.exit()
    args = parseArguments()

    sol = args.circ
    if not os.path.isfile(sol): sys.exit("Please, specify a valid path to circumscriptino. File '" + sol + "' does not exist.")
    if not os.access(sol, os.X_OK): sys.exit("Please, specify a valid path to circumscriptino. File '" + sol + "' is not executable.")

    if args.fo is None: sys.exit("Please, specify a format.")
    if args.p is None: sys.exit("Please, specify a problem.")
    if args.f is None: sys.exit("Please, specify an input file.")
    #if args.p[-2:] == '-D':
    #    if args.m is None: sys.exit("Please, specify an input file (for dynamic changes).")
    #elif args.m is not None: sys.exit("Option -m can be used only with dynamic problems.")

    if not args.fo in parseFunctions: sys.exit("Unsupported format: " + args.fo)
    if not args.p in problemFunctions: sys.exit("Unsupported problem: " + args.p)

    parseFunctions[args.fo](args.f)
    #if args.m: parseDynFunctions[args.fo](args.m)
    if args.a:
        problemFunctions[args.p](args.a, print_only=args.print_circ)
    else:
        problemFunctions[args.p](print_only=args.print_circ)
