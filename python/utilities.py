from collections import OrderedDict
from itertools import chain, combinations

class OrderedSet:
    def __init__(self): self.data = OrderedDict()
    def add(self, value): self.data[value] = None
    def __iter__(self):
        for key in self.data: yield key

def powerset(iterable, min_size=0):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(min_size, len(s)+1))