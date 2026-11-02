# SPDX-FileCopyrightText: 2026 Mattia Egloff <mattia.egloff@pm.me>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Optional

from .tree import Node, Tree
from .task import Task
from .parse import parse_tree


@dataclass
class TaskCounts:
    total: int
    done: int
    remaining: int


def trickle_completion(tree: Tree[Task]):
    """
    Trickle-down completion from parent to children.
    If a node is done, all its progeny are also marked done.
    """
    def recurse(node: Node[Task], done: Optional[bool] = None):
        if done:
            node.value.done = True
        for child in node.children:
            recurse(child, done=node.value.done)

    for root in tree.roots:
        recurse(root)


def count_tasks(plan) -> TaskCounts:
    tree = parse_tree(plan)
    trickle_completion(tree)
    leaves = list(tree.leaves)
    total = len(leaves)
    remaining = len([leaf for leaf in leaves if not leaf.value.done])
    done = total - remaining
    return TaskCounts(total=total, done=done, remaining=remaining)


def count_all_tasks(plan):
    return count_tasks(plan).total


def count_remaining_tasks(plan):
    return count_tasks(plan).remaining