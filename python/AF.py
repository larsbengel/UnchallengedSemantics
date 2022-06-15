from collections import OrderedDict
from utilities import OrderedSet

class AF:
    def __init__(self):
        # the arguments of the AF
        self.arg = set()
        # the attack relation of the AF, stored in the form of the sets a⁺ and a⁻ for every argument a in AF
        self.attacḱed = OrderedDict()
        self.attacḱers = OrderedDict()
        # dictionary to store the integer representation for each argument
        #self.argToIdx = {}

    def addArgument(self, name):
        #if name not in self.argToIdx:
        #    self.argToIdx[name] = len(self.arg)
            self.arg.add(name)

    def addAttack(self, a, b):
        if a not in self.attacḱed: 
            self.attacḱed[a] = set()
        self.attacḱed[a].add(b)

        if b not in self.attacḱers: 
            self.attacḱers[b] = set()
        self.attacḱers[b].add(a)

    def getAttacked(self, a):
        return self.attacḱed.get(a, ())

    def getAttackers(self, a):
        return self.attacḱers.get(a, ())

    def getAttackersSet(self, S):
        atts = set()
        for a in S:
            atts.update(self.getAttackers(a))
        return atts

    def getReduct(args):
        pass