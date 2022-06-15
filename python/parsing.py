import fileinput
import imp
import re
from AF import AF

# parse an AF from a .tgf file
def parseTGF(filename):
    af = AF()

    sharp = False
    for line in fileinput.input(filename):
        line = line.strip()
        if not line: continue
        if line == '#':
            sharp = True
        elif not sharp:
            name = line
            af.addArgument(name)
        else:
            (a, b) = line.split()
            af.addAttack(a, b)

    return af

# parse an AF from a .apx file
def parseAPX(filename):
    af = AF()
    for line in fileinput.input(filename):
        res = parseAPX.re_atom.match(line)
        if not res: continue
        pred = res.group('predicate')
        if pred == 'arg':
            name = res.group('args')[1:]
            af.addArgument(name)
        elif pred == 'att':
            (a, b) = [x.strip()[1:] for x in res.group('args').split(',')]

            af.addAttack(a, b)

    return af
parseAPX.re_atom = re.compile('(?P<predicate>\w+)\s*\((?P<args>[\w,\s]+)\)\.')

parseFunctions = {"tgf" : parseTGF, "apx" : parseAPX}