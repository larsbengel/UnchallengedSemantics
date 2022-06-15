#!/usr/bin/env python3

GPL = """
AF solver.
Copyright (C) 2022  Lars Bengel (lars.bengel@fernuni-hagen.de)

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

VERSION = "0.1"

import argparse
import sys
import os

from solver import Solver
from parsing import parseFunctions
from utilities import powerset

def parseArguments():
    global VERSION
    global GPL
    parser = argparse.ArgumentParser(description=GPL.split("\n")[1], epilog="Copyright (C) 2022  Lars Bengel (lars.bengel@fernuni-hagen.de)")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION, help='print version number')
    parser.add_argument('--formats', action='store_true', help='print supported formats and exit')
    parser.add_argument('--problems', action='store_true', help='print supported computational problems and exit')
    parser.add_argument('-p', metavar='<task>', type=str, help='')
    parser.add_argument('-f', metavar='<file>', type=str, help='')
    parser.add_argument('-fo', metavar='<fileformat>', type=str, help='')
    parser.add_argument('-a', metavar='<additional_parameter>', type=str, help='')
    parser.add_argument('--solv', metavar='<file>', type=str, help='path to SAT solver (default is glucose-static in the script directory)')
    parser.add_argument('--print-solv', action='store_true', help='print numeric format for SAT-solver and exit')
    args = parser.parse_args()
    if args.formats:
        print('[%s]' % ','.join(sorted(parseFunctions.keys())))
        sys.exit()
    #if args.problems:
    #    print('[%s]' % ','.join(sorted(problemFunctions.keys())))
    #    sys.exit()
    if not args.solv: args.solv = os.path.dirname(os.path.realpath(__file__)) + '/glucose_static'
    return args

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(sys.argv[0], VERSION)
        print("Lars Bengel")
        sys.exit()
    args = parseArguments()

    sol = args.solv
    if not os.path.isfile(sol): sys.exit("Please, specify a valid path to solver. File '" + sol + "' does not exist.")
    if not os.access(sol, os.X_OK): sys.exit("Please, specify a valid path to solver. File '" + sol + "' is not executable.")

    if args.fo is None: sys.exit("Please, specify a format.")
    if args.p is None: sys.exit("Please, specify a problem.")
    if args.f is None: sys.exit("Please, specify an input file.")

    if not args.fo in parseFunctions: sys.exit("Unsupported format: " + args.fo)
    #if not args.p in problemFunctions: sys.exit("Unsupported problem: " + args.p)

    solver = Solver(args.f, args.fo, sol)
    #for S in powerset(solver.af.arg):
    S = ['1']
    s = ''.join(S)
    solver.DE_UC(S, "%s.txt" %s)
    solver.solve("%s.txt" %s)

