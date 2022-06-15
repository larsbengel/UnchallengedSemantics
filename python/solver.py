from semantic_encodings import *
from parsing import parseFunctions
import sys
import subprocess

from utilities import powerset

class Solver:
    def __init__(self, file, format, sol):
        self.af = parseFunctions[format](file)
        self.sol = sol

    def DE_UC(self, S, file="encoding.tmp"):
        self.stream = open(file, 'w+b')
        #preamble(self.stream, len(self.af.arg), 0)
        self.necessary_subset(S)
        self.sufficient_subset(S)
        result = self.initial(S)
        if not result:
            print("UNSATISFIABLE")
        self.stream.close()

    def solve(self, file="encoding.tmp"):
        with subprocess.Popen([self.sol, file], stdout=subprocess.PIPE) as proc:
            result = proc.stdout.readlines()[-1]
            print(result)

        # encode the neccesary condition for the set S
    def necessary_subset(self, S):
        for a in S:
            self.stream.write(('%s 0\n' %a).encode())

    # encode the sufficient condition for the set S
    def sufficient_subset(self, S):
        for a in self.af.arg:
            if a not in S:
                self.stream.write(('%s 0\n' %neg(a)).encode())

    def conflictfree(self, S):
        for a in S:
            for b in self.af.getAttacked(a):
                self.stream.write(('%s 0\n' %neg(b)).encode())

    def admissible(self, S):
        self.conflictfree(S)
        for a in self.af.getAttackersSet(S):
            self.stream.write((' '.join(self.af.getAttackers(a)) + " 0\n").encode())

    def empty(self, S):
        for a in S:
            self.stream.write(('%s 0\n' %neg(a)).encode())

    def non_empty(self, S):
        self.stream.write((' '.join(S) + " 0\n").encode())

    def minimality(self, S):
        for X in powerset(self.af.arg):
            X = set(X)
            if X.issubset(S) and not set(S).issubset(X):
                print(X)

    def initial(self, S):
        self.admissible(S)
        # every true subset of S is not admissible
        no_smaller_adm_set = True
        for X in powerset(self.af.arg, min_size=1):
            X = set(X)
            if X.issubset(S) and not set(S).issubset(X):
                adm = True
                for a in X:
                    for b in self.af.getAttacked(a):
                        if b in X:
                            adm = False
                
                for a in self.af.getAttackersSet(X):
                    a_disabled = False
                    for b in self.af.getAttackers(a):
                        if b in X:
                            a_disabled = True
                    if not a_disabled:
                        adm = False

                if adm:
                    return False
        
        return True

    def emptyAndNoSelectableSets(self, S):
        self.empty(S)
        for X in powerset(self.af.arg, min_size=1):
            pass
