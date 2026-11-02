from functools import reduce
import math


def gcd(*numbers):
    return reduce(math.gcd, numbers)


def find_groups(string, grouper):
    """
    Returns a list of texts enclosed in grouper.

    E.g.
        find_groups('hello {there}', '{}') -> ['there']

    Unclosed groups are silently skipped.
    """
    starter = grouper[0]
    finisher = grouper[1]
    groups = []
    while starter in string:
        i1 = string.index(starter) + len(starter)
        rest = string[i1:]
        if finisher not in rest:
            break
        i2 = rest.index(finisher)
        groups.append(rest[:i2])
        string = rest[i2 + len(finisher):]
    return groups


def pipe(functions):
    return lambda x: reduce(lambda a, v: v(a), functions, x)
