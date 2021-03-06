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
import subprocess
import sys
import tempfile

class OrderedSet:
    def __init__(self): self.data = OrderedDict()
    def add(self, value): self.data[value] = None
    def __iter__(self):
        for key in self.data: yield key

arg = [None]
argToIdx = {}
att = OrderedDict()
attR = OrderedDict()

dynAtt = OrderedDict()
dynAttList = []

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

def parseTGF(filename):
    sharp = False
    for line in fileinput.input(filename):
        line = line.strip()
        if not line: continue
        if line == '#':
            sharp = True
        elif not sharp:
            name = line
            if name not in argToIdx:
                argToIdx[name] = len(arg)
                arg.append(name)
        else:
            (a, b) = line.split()

            if a not in att: att[a] = OrderedSet()
            att[a].add(b)

            if b not in attR: attR[b] = OrderedSet()
            attR[b].add(a)

def parseAPX(filename):
    for line in fileinput.input(filename):
        res = parseAPX.re_atom.match(line)
        if not res: continue
        pred = res.group('predicate')
        if pred == 'arg':
            name = res.group('args')
            if name not in argToIdx:
                argToIdx[name] = len(arg)
                arg.append(name)
        elif pred == 'att':
            (a, b) = [x.strip() for x in res.group('args').split(',')]

            if a not in att: att[a] = OrderedSet()
            att[a].add(b)

            if b not in attR: attR[b] = OrderedSet()
            attR[b].add(a)
parseAPX.re_atom = re.compile('(?P<predicate>\w+)\s*\((?P<args>[\w,\s]+)\)\.')

def parseTGFM(filename):
    for line in fileinput.input(filename):
        line = line.strip()
        if not line: continue
        sign = line[0] == '+'
        (a, b) = line[1:].split()

        dynAttList.append((sign, a, b))
        if (a,b) not in dynAtt: dynAtt[(a,b)] = a in att and b in att[a]

        if a not in att: att[a] = OrderedSet()
        att[a].add(b)

        if b not in attR: attR[b] = OrderedSet()
        attR[b].add(a)

def parseAPXM(filename):
    for line in fileinput.input(filename):
        res = parseAPXM.re_atom.match(line)
        if not res: continue
        sign = res.group('sign')
        pred = res.group('predicate')
        if pred == 'att':
            (a, b) = [x.strip() for x in res.group('args').split(',')]

            dynAttList.append((sign, a, b))
            if (a,b) not in dynAtt: dynAtt[(a,b)] = a in att and b in att[a]

            if a not in att: att[a] = OrderedSet()
            att[a].add(b)

            if b not in attR: attR[b] = OrderedSet()
            attR[b].add(a)
parseAPXM.re_atom = re.compile('(?P<sign>[+-])(?P<predicate>\w+)\s*\((?P<args>[\w,\s]+)\)\.')

parseFunctions = {"tgf" : parseTGF, "apx" : parseAPX}
parseDynFunctions = {"tgf" : parseTGFM, "apx" : parseAPXM}

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

def conflictFree(stream):
    for a in att:
        for b in att[a]:
            if (a,b) in dynAtt: stream.write(("%d %d %d 0\n" % (-attack(a, b), -argToIdx[a], -argToIdx[b])).encode())
            else: stream.write(("%d %d 0\n" % (-argToIdx[a], -argToIdx[b])).encode())

# def conflictFreeViaAttacked(stream):
#     for a in arg[1:]:
#         stream.write(("%d %d 0\n" % (-attacked(a), -argToIdx[a])).encode())

def buildAttacked(stream):
    for b in arg[1:]:
        cl = [str(-attacked(b))]
        if b in attR:
            for c in attR[b]:
                if (c,b) in dynAtt:
                    cl.append(str(attackAndAttacker(c, b)))
                    stream.write(("%d %d 0\n" % (-attackAndAttacker(c, b), attacked(b))).encode())
                else:
                    cl.append(str(argToIdx[c]))
                    stream.write(("%d %d 0\n" % (-argToIdx[c], attacked(b))).encode())
        stream.write((' '.join(cl) + ' 0\n').encode())

def admissible(stream):
    for b in att:
        for a in att[b]:
            if (b,a) in dynAtt:
                stream.write(("%d %d %d 0\n" % (-attack(b, a), -argToIdx[a], attacked(b))).encode())
            else:
                stream.write(("%d %d 0\n" % (-argToIdx[a], attacked(b))).encode())

def complete(stream):
    for a in arg[1:]:
        cl = [str(argToIdx[a])]
        if a in attR:
            for b in attR[a]:
                if (b,a) in dynAtt:
                    cl.append(str(-defended(b, a)))
                else:
                    cl.append(str(-attacked(b)))
        stream.write((' '.join(cl) + ' 0\n').encode())

def stable(stream):
    for a in arg[1:]:
        cl = [str(argToIdx[a])]
        if a in attR:
            for b in attR[a]:
                if (b,a) in dynAtt:
                    cl.append(str(attackAndAttacker(b, a)))
                else:
                    cl.append(str(argToIdx[b]))
        stream.write((' '.join(cl) + ' 0\n').encode())

def buildRange(stream):
    for a in arg[1:]:
        cl = [str(-inRange(a)), str(argToIdx[a])]
        #stream.write(('%d %d 0\n' % (inRange(a), -argToIdx[a])).encode())
        if a in attR:
            for b in attR[a]:
                if (b,a) in dynAtt:
                    cl.append(str(attackAndAttacker(b, a)))
                else:
                    cl.append(str(argToIdx[b]))
                #stream.write(('%d %d 0\n' % (inRange(a), -argToIdx[b])).encode())
        stream.write((' '.join(cl) + ' 0\n').encode())

# def buildRangeViaAttacked(stream):
#     for a in arg[1:]:
#         cl = [str(-inRange(a)), str(argToIdx[a]), str(attacked(a))]
#         stream.write((' '.join(cl) + ' 0\n').encode())

def buildAttackAndAttacked(stream):
    for (a,b) in dynAtt:
        stream.write(("%d %d 0\n" % (-attackAndAttacker(a, b), attack(a, b))).encode())
        stream.write(("%d %d 0\n" % (-attackAndAttacker(a, b), argToIdx[a])).encode())
        stream.write(("%d %d %d 0\n" % (attackAndAttacker(a, b), -attack(a, b), -argToIdx[a])).encode())

def buildDefended(stream):
    for (a,b) in dynAtt:
        stream.write(("%d %d %d 0\n" % (-defended(a, b), -attack(a, b), attacked(a))).encode())
        stream.write(("%d %d 0\n" % (defended(a, b), attack(a, b))).encode())
        stream.write(("%d %d 0\n" % (defended(a, b), -attacked(a))).encode())

def buildAssumptions(stream):
    if not dynAttList: return

    state = OrderedDict(dynAtt)
    last = {}

    i = 0
    for (s,a,b) in dynAttList:
        i += 1
        last[(a,b)] = i

    ass = []
    for (a,b) in state:
        ass.append(str(attack(a, b) if state[(a,b)] else -attack(a, b)))
    stream.write(("s %s 0\n" % (' '.join(ass))).encode())

    i = 0
    for (s,a,b) in dynAttList:
        i += 1
        state[(a,b)] = s

        if last[(a,b)] == i:
            stream.write(("a %d 0\n" % (attack(a, b) if state[(a,b)] else -attack(a, b))).encode())
            del state[(a,b)]

        ass = []
        for (a,b) in state:
            ass.append(str(attack(a, b) if state[(a,b)] else -attack(a, b)))
        stream.write(("s %s 0\n" % (' '.join(ass))).encode())


def credulous(stream, a):
    stream.write(("q %d\n" % (argToIdx[a],)).encode())
    stream.write("v no ids\n".encode())
    stream.write("v iterations start:{}\n".format('[' if dynAttList else '').encode())
    stream.write("v iterations end:{}\\n\n".format(']' if dynAttList else '').encode())
    stream.write("v iteration start:\n".encode())
    stream.write("v iteration sep:, \n".encode())
    stream.write("v iteration end:\n".encode())
    stream.write("v models unknown:\n".encode())
    stream.write("v models none:NO\n".encode())
    stream.write("v models start:YES\n".encode())
    stream.write("v models end:\n".encode())
    stream.write("v model start:\n".encode())
    stream.write("v model sep:\n".encode())
    stream.write("v model end:\n".encode())
    stream.write("v lit start:\n".encode())
    stream.write("v lit sep:\n".encode())
    stream.write("v lit end:\n".encode())

def skeptical(stream, a):
    stream.write(("q -%d\n" % (argToIdx[a],)).encode())
    stream.write("v no ids\n".encode())
    stream.write("v iterations start:{}\n".format('[' if dynAttList else '').encode())
    stream.write("v iterations end:{}\\n\n".format(']' if dynAttList else '').encode())
    stream.write("v iteration start:\n".encode())
    stream.write("v iteration sep:, \n".encode())
    stream.write("v iteration end:\n".encode())
    stream.write("v models unknown:\n".encode())
    stream.write("v models none:YES\n".encode())
    stream.write("v models start:NO\n".encode())
    stream.write("v models end:\n".encode())
    stream.write("v model start:\n".encode())
    stream.write("v model sep:\n".encode())
    stream.write("v model end:\n".encode())
    stream.write("v lit start:\n".encode())
    stream.write("v lit sep:\n".encode())
    stream.write("v lit end:\n".encode())

def single(stream):
    nameTable(stream)
    stream.write("v no ids\n".encode())
    stream.write("v iterations start:{}\n".format('[\\n' if dynAttList else '').encode())
    stream.write("v iterations end:{}\\n\n".format('\\n]' if dynAttList else '').encode())
    stream.write("v iteration start:{}\n".format('    ' if dynAttList else '').encode())
    stream.write("v iteration sep:\\n\n".encode())
    stream.write("v iteration end:\n".encode())
    stream.write("v models unknown:\n".encode())
    stream.write("v models none:{}\n".format('[]' if dynAttList else 'NO').encode())
    stream.write("v models start:\n".encode())
    stream.write("v models end:\n".encode())
    stream.write("v model start:[\n".encode())
    stream.write("v model sep:\n".encode())
    stream.write("v model end:]\n".encode())
    stream.write("v lit start:\n".encode())
    stream.write("v lit sep:,\n".encode())
    stream.write("v lit end:\n".encode())

def enumerate(stream):
    nameTable(stream)
    stream.write("v no ids\n".encode())
    stream.write("v iterations start:{}\n".format('[\\n' if dynAttList else '').encode())
    stream.write("v iterations end:{}\\n\n".format('\\n]' if dynAttList else '').encode())
    stream.write("v iteration start:\n".encode())
    stream.write("v iteration sep:\\n\n".encode())
    stream.write("v iteration end:\n".encode())
    stream.write("v models unknown:\n".encode())
    stream.write("v models none:[]\n".encode())
    stream.write("v models start:{}[\\n\n".format('    ' if dynAttList else '').encode())
    stream.write("v models end:{}]\n".format('    ' if dynAttList else '').encode())
    stream.write("v model start:{}    [\n".format('    ' if dynAttList else '').encode())
    stream.write("v model sep:\n".encode())
    stream.write("v model end:]\\n\n".encode())
    stream.write("v lit start:\n".encode())
    stream.write("v lit sep:,\n".encode())
    stream.write("v lit end:\n".encode())

def count_extensions(stream):
    noNameTable(stream)
    stream.write("v no ids\n".encode())
    stream.write("v iterations start:\n".encode())
    stream.write("v iterations end:\n".encode())
    stream.write("v iteration start:\n".encode())
    stream.write("v iteration sep:\\n\n".encode())
    stream.write("v iteration end:\n".encode())
    stream.write("v models unknown:\n".encode())
    stream.write("v models none:0\n".encode())
    stream.write("v models start:\n".encode())
    stream.write("v models end:#\n".encode())
    stream.write("v model start:\n".encode())
    stream.write("v model sep:\n".encode())
    stream.write("v model end:\n".encode())
    stream.write("v lit start:\n".encode())
    stream.write("v lit sep:\n".encode())
    stream.write("v lit end:\n".encode())

def post_process(stream):
    nameTable(stream)
    stream.write("v no ids\n".encode())
    stream.write("v iterations start:{}\n".format('[' if dynAttList else '').encode())
    stream.write("v iterations end:{}\\n\n".format(']' if dynAttList else '').encode())
    stream.write("v iteration start:\n".encode())
    stream.write("v iteration sep:\\n\n".encode())
    stream.write("v iteration end:\n".encode())
    stream.write("v models none:\\n\n".encode())
    stream.write("v models start:\n".encode())
    stream.write("v models end:\\n\n".encode())
    stream.write("v model start:\n".encode())
    stream.write("v model sep:\\n\n".encode())
    stream.write("v model end:\n".encode())
    stream.write("v lit start:\n".encode())
    stream.write("v lit sep: \n".encode())
    stream.write("v lit end:\n".encode())

def nameTable(stream):
    for i in range(1, len(arg)):
        stream.write(('v %d %s\n' % (i, arg[i])).encode())

def noNameTable(stream):
    for i in range(1, len(arg)):
        stream.write(('v %d\n' % (i,)).encode())

def preamble(stream, soft=[]):
    stream.write('p circ\n'.encode())
    for s in soft: stream.write(('w %d\n' % (s,)).encode())

def CO(stream):
    preamble(stream)
    conflictFree(stream)
    buildAttacked(stream)
    admissible(stream)
    complete(stream)
    buildAttackAndAttacked(stream)
    buildDefended(stream)
    buildAssumptions(stream)

def ST(stream):
    preamble(stream)
    conflictFree(stream)
    buildAttacked(stream)
    admissible(stream)
    complete(stream)
    stable(stream)
    buildAttackAndAttacked(stream)
    buildDefended(stream)
    buildAssumptions(stream)

def PR(stream):
    preamble(stream, range(1, len(arg)))
    conflictFree(stream)
    buildAttacked(stream)
    admissible(stream)
    complete(stream)
    buildAttackAndAttacked(stream)
    buildDefended(stream)
    buildAssumptions(stream)

def GR(stream):
    preamble(stream, [-x for x in range(1, len(arg))])
    conflictFree(stream)
    buildAttacked(stream)
    admissible(stream)
    complete(stream)
    buildAttackAndAttacked(stream)
    buildDefended(stream)
    buildAssumptions(stream)

def SST(stream):
    preamble(stream, [inRange(i) for i in arg[1:]])
    conflictFree(stream)
    buildAttacked(stream)
    admissible(stream)
    complete(stream)
    buildRange(stream)
    buildAttackAndAttacked(stream)
    buildDefended(stream)
    buildAssumptions(stream)

def STG(stream):
    preamble(stream, [inRange(i) for i in arg[1:]])
    conflictFree(stream)
    buildRange(stream)
    buildAttackAndAttacked(stream)
    buildDefended(stream)
    buildAssumptions(stream)

def close(stream):
    stream.write('n 0\n'.encode())
    stream.close()

def DC_CO(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    CO(stream)
    credulous(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def DS_CO(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    CO(stream)
    skeptical(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def SE_CO(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    CO(stream)
    single(stream)
    close(stream)
    if not print_only: printAll(solver)

def EE_CO(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=0', '--circ-wit=0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    CO(stream)
    enumerate(stream)
    close(stream)
    if not print_only: printAll(solver)

def CE_CO(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=0', '--circ-wit=0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    CO(stream)
    count_extensions(stream)
    close(stream)
    if not print_only: printAll(solver)

def DC_PR(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    PR(stream)
    credulous(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def DS_PR(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    PR(stream)
    skeptical(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def SE_PR(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    PR(stream)
    single(stream)
    close(stream)
    if not print_only: printAll(solver)

def EE_PR(end='\n', print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=0', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    PR(stream)
    enumerate(stream)
    close(stream)
    if not print_only: printAll(solver)

def CE_PR(end='\n', print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=0', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    PR(stream)
    count_extensions(stream)
    close(stream)
    if not print_only: printAll(solver)

def DC_ST(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    ST(stream)
    credulous(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def DS_ST(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    ST(stream)
    skeptical(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def SE_ST(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    ST(stream)
    single(stream)
    close(stream)
    if not print_only: printAll(solver)

def EE_ST(end='\n', print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=0', '--circ-wit=0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    ST(stream)
    enumerate(stream)
    close(stream)
    if not print_only: printAll(solver)

def CE_ST(end='\n', print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=0', '--circ-wit=0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    ST(stream)
    count_extensions(stream)
    close(stream)
    if not print_only: printAll(solver)

def DC_SST(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    SST(stream)
    credulous(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def DS_SST(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    SST(stream)
    skeptical(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def SE_SST(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    SST(stream)
    single(stream)
    close(stream)
    if not print_only: printAll(solver)

def EE_SST(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=0', '--circ-wit=0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    SST(stream)
    enumerate(stream)
    close(stream)
    if not print_only: printAll(solver)

def CE_SST(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=0', '--circ-wit=0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    SST(stream)
    count_extensions(stream)
    close(stream)
    if not print_only: printAll(solver)

def DC_STG(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    STG(stream)
    credulous(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def DS_STG(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    STG(stream)
    skeptical(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def SE_STG(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    STG(stream)
    single(stream)
    close(stream)
    if not print_only: printAll(solver)

def EE_STG(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=0', '--circ-wit=0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    STG(stream)
    enumerate(stream)
    close(stream)
    if not print_only: printAll(solver)

def CE_STG(print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=0', '--circ-wit=0'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    STG(stream)
    count_extensions(stream)
    close(stream)
    if not print_only: printAll(solver)

def DC_GR(a, print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1', '--no-pre'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #solver = subprocess.Popen([sol, '--circ-propagate'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    GR(stream)
    credulous(stream, a)
    close(stream)
    if not print_only: printAll(solver)

def SE_GR(end='\n', print_only=False):
    stream = sys.stdout.buffer
    if not print_only:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1', '--no-pre'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #solver = subprocess.Popen([sol, '--circ-propagate'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stream = solver.stdin
    GR(stream)
    single(stream)
    close(stream)
    if not print_only: printAll(solver)

def computeUnionOfAdmissibleSets():
    union = set()
    while True:
        solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        preamble(solver.stdin, [i for i in range(1, len(arg)) if arg[i] not in union])
        conflictFree(solver.stdin)
        buildAttacked(solver.stdin)
        admissible(solver.stdin)
        post_process(solver.stdin)
        close(solver.stdin)
        stop = True
        while True:
            line = solver.stdout.readline()
            if not line: break
            line = line.decode().strip().split()
            for a in line:
                if a in union: continue
                union.add(a)
                stop = False
        if stop: break
    return union

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

def DC_ID(query_arg, print_only=False):
    if print_only:
        print("DC-ID is not solved with a single call.")
        sys.exit()

    union = computeUnionOfAdmissibleSets()
    attacked = computeAttackedBy(union)
    if query_arg in attacked:
        print('NO')
        return

    # find maximal admissible set that is not attacked by the union
    solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    preamble(solver.stdin, [argToIdx[a] for a in arg[1:] if a not in attacked])
    conflictFree(solver.stdin)
    buildAttacked(solver.stdin)
    admissible(solver.stdin)
    credulous(solver.stdin, query_arg)
    for a in attacked: solver.stdin.write((str(-argToIdx[a]) + ' 0\n').encode())
    close(solver.stdin)
    printAll(solver)

def SE_ID(print_only=False):
    if print_only:
        print("SE-ID is not solved with a single call.")
        sys.exit()

    union = computeUnionOfAdmissibleSets()
    attacked = computeAttackedBy(union)

    # find maximal admissible set that is not attacked by the union
    solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    preamble(solver.stdin, [argToIdx[a] for a in arg[1:] if a not in attacked])
    conflictFree(solver.stdin)
    buildAttacked(solver.stdin)
    admissible(solver.stdin)
    single(solver.stdin)
    for a in attacked: solver.stdin.write((str(-argToIdx[a]) + ' 0\n').encode())
    close(solver.stdin)
    printAll(solver)

def isStable(e):
    for a in arg[1:]:
        if a in e: continue
        if a not in attR: continue
        ok = False
        for b in attR[a]:
            if b in e:
                ok = True
                break
        if not ok: return False
    return True

# GR is contained in the intersection of PR, and ST is a subset of PR.
# Hence, we first compute GR, then force truth of GR and enumerate PR.
# For each extension in PR, stability is checked.
# def D3(print_only=False):
#     if print_only:
#         print("D3 is not solved with a single call.")
#         sys.exit()
#
#     solver = subprocess.Popen([sol, '-n=1', '--circ-wit=1', '--no-pre'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
#     GR(solver.stdin)
#     post_process(solver.stdin)
#     close(solver.stdin)
#     gr = None
#     while True:
#         line = solver.stdout.readline()
#         if not line: break
#         assert gr is None
#         gr = line.decode().strip().split()
#
#     assert gr is not None
#     print('[', end='')
#     printModel(gr)
#     print('],', end='')
#     sys.stdout.flush()
#
#     solver = subprocess.Popen([sol, '-n=0', '--circ-wit=1'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
#     PR(solver.stdin)
#     for a in gr: solver.stdin.write((str(argToIdx[a]) + ' 0\n').encode())
#     post_process(solver.stdin)
#     close(solver.stdin)
#     print('[', end='')
#     count = 0
#     pr = []
#     while True:
#         line = solver.stdout.readline()
#         if not line: break
#         line = line.decode().strip().split()
#         if line:
#             pr.append(line)
#             if isStable(line):
#                 if count != 0: print(',', end='')
#                 count += 1
#                 printModel(line)
#     print('],', end='')
#     sys.stdout.flush()
#
#     print('[', end='')
#     count = 0
#     for m in pr:
#         if count != 0: print(',', end='')
#         count += 1
#         printModel(m)
#     print(']')

problemFunctions = {
    "DC-CO" : DC_CO, "DS-CO" : DS_CO, "SE-CO" : SE_CO, "CE-CO" : CE_CO,
    "DC-PR" : DC_PR, "DS-PR" : DS_PR, "SE-PR" : SE_PR, "CE-PR" : CE_PR,
    "DC-ST" : DC_ST, "DS-ST" : DS_ST, "SE-ST" : SE_ST, "CE-ST" : CE_ST,
    "DC-SST" : DC_SST, "DS-SST" : DS_SST, "SE-SST" : SE_SST, "CE-SST" : CE_SST,
    "DC-STG" : DC_STG, "DS-STG" : DS_STG, "SE-STG" : SE_STG, "CE-STG" : CE_STG,
    "DS-ID" : DC_ID, "SE-ID" : SE_ID,

#    "DC-CO" : DC_CO, "DS-CO" : DS_CO, "SE-CO" : SE_CO, "EE-CO" : EE_CO,
#    "DC-PR" : DC_PR, "DS-PR" : DS_PR, "SE-PR" : SE_PR, "EE-PR" : EE_PR,
#    "DC-ST" : DC_ST, "DS-ST" : DS_ST, "SE-ST" : SE_ST, "EE-ST" : EE_ST,
#    "DC-SST" : DC_SST, "DS-SST" : DS_SST, "SE-SST" : SE_SST, "EE-SST" : EE_SST,
#    "DC-STG" : DC_STG, "DS-STG" : DS_STG, "SE-STG" : SE_STG, "EE-STG" : EE_STG,
#    "DC-GR" : DC_GR, "SE-GR" : SE_GR,
#    "DC-ID" : DC_ID, "SE-ID" : SE_ID,

#    "D3": D3

#    "DC-CO-D" : DC_CO, "DS-CO-D" : DS_CO, "SE-CO-D" : SE_CO, "EE-CO-D" : EE_CO,
#    "DC-PR-D" : DC_PR, "DS-PR-D" : DS_PR, "SE-PR-D" : SE_PR, "EE-PR-D" : EE_PR,
#    "DC-ST-D" : DC_ST, "DS-ST-D" : DS_ST, "SE-ST-D" : SE_ST, "EE-ST-D" : EE_ST,
    #"DC-SST-D" : DC_SST, "DS-SST-D" : DS_SST, "SE-SST-D" : SE_SST, "EE-SST-D" : EE_SST,
    #"DC-STG-D" : DC_STG, "DS-STG-D" : DS_STG, "SE-STG-D" : SE_STG, "EE-STG-D" : EE_STG,
#    "DC-GR-D" : DC_GR, "SE-GR-D" : SE_GR,
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

    if not args.fo in parseFunctions: sys.exit("Unsopported format: " + args.fo)
    if not args.p in problemFunctions: sys.exit("Unsopported problem: " + args.p)

    parseFunctions[args.fo](args.f)
    #if args.m: parseDynFunctions[args.fo](args.m)
    if args.a:
        problemFunctions[args.p](args.a, print_only=args.print_circ)
    else:
        problemFunctions[args.p](print_only=args.print_circ)
