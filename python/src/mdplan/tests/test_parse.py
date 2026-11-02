# SPDX-FileCopyrightText: 2026 Mattia Egloff <mattia.egloff@pm.me>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from ..parse import is_task, parse_task, parse_tree, infer_indent
from ..utils import find_groups


class TestFindGroups:
    def test_returns_matched_groups(self):
        assert find_groups("hello @(world)", ["@(", ")"]) == ["world"]

    def test_returns_empty_for_no_match(self):
        assert find_groups("hello world", ["@(", ")"]) == []

    def test_skips_unclosed_delimiter(self):
        result = find_groups("hello @(world", ["@(", ")"])
        assert result == []

    def test_handles_mixed_closed_and_unclosed(self):
        result = find_groups("@(a) then @(b", ["@(", ")"])
        assert result == ["a"]


class TestIsTask:
    def test_recognizes_list_item(self):
        line = "- hello"
        assert is_task(line)
        line = "1. hello"
        assert is_task(line), "Could not recognize numbered task"
        line = "  1. hello"
        assert is_task(line), "Could not recognize task with indentation"

    def test_recognizes_header(self):
        line = "# hello"
        assert is_task(line)
        line = "## hello"
        assert is_task(line), "Could not recognize h2 as task"

    def test_ignores_block_quote(self):
        line = "> * hello"
        assert not is_task(line)

    def test_ignores_horizontal_line(self):
        line = "***"
        assert not is_task(line)


class TestParseTask:
    def test_captures_description(self):
        line = "  - hello @(world)"
        task = parse_task(line)
        assert task.description == "hello"

    def test_description_excludes_done(self):
        line = "- [x] hello"
        task = parse_task(line)
        assert task.description == "hello"

    def test_description_excludes_empty_checkbox(self):
        line = "- [ ] hello"
        task = parse_task(line)
        assert task.description == "hello"

    def test_captures_is_done(self):
        line = "- [x] hello"
        task = parse_task(line)
        assert task.done

    def test_captures_empty_done(self):
        line = "- [ ] hello"
        task = parse_task(line)
        assert not task.done

    def test_captures_dependencies(self):
        line = "- [x] hello @(world, universe)"
        task = parse_task(line)
        assert "world" in task.dependencies
        assert "universe" in task.dependencies

    def test_captures_multiple_dependency_blocks(self):
        line = "- [ ] hello @(alpha) @(beta)"
        task = parse_task(line)
        assert "alpha" in task.dependencies
        assert "beta" in task.dependencies

    def test_captures_mixed_dependency_syntax(self):
        line = "- [ ] hello @(alpha, beta)@(gamma)"
        task = parse_task(line)
        assert "alpha" in task.dependencies
        assert "beta" in task.dependencies
        assert "gamma" in task.dependencies


class TestParseTree:
    def test_contains_appropriate_leaves(self):
        plan = """
- one
  - two
"""
        tree = parse_tree(plan)
        assert len(tree.leaves) == 1
        assert tree.leaves.pop().value.description == "two"

    def test_correctly_finds_children(self):
        plan = """
- parent
  - child1
  - child2
"""
        tree = parse_tree(plan)
        parent = [node for node in tree.nodes if node.value.description == "parent"][0]
        assert len(parent.children) == 2

    def test_ignores_code_blocks(self):
        plan = """
- task1
```
- task2
```
"""
        tree = parse_tree(plan)
        assert len(tree.nodes) == 1

    def test_joins_multiline_continuation(self):
        plan = """
1. [x] Wire DeliveryService into RelayClient @(DeliveryService
   — ACK)
2. [x] Next task @(Wire DeliveryService)
"""
        tree = parse_tree(plan)
        assert len(tree.nodes) == 2
        wire_task = [n for n in tree.nodes if "Wire DeliveryService" in n.value.description][0]
        assert "DeliveryService — ACK" in wire_task.value.dependencies

    def test_joins_multiline_multiple_deps(self):
        plan = """
1. [x] Phase 1 verification gate @(connectivity
   events)@(expiration cleanup)
"""
        tree = parse_tree(plan)
        assert len(tree.nodes) == 1
        task = tree.nodes.pop()
        assert "connectivity events" in task.value.dependencies
        assert "expiration cleanup" in task.value.dependencies

    def test_multiline_does_not_eat_next_task(self):
        plan = """
1. [x] First @(dep
   continued)
2. [x] Second
3. [x] Third
"""
        tree = parse_tree(plan)
        assert len(tree.nodes) == 3

    def test_allows_for_indentation_jumps(self):
        # some markdown formatters do this by default
        plan = """
1. first
   - second
     - third
   - fourth
"""
        tree = parse_tree(plan)
        assert len(tree.roots) == 1
        assert len(tree.leaves) == 2
        first = tree.roots.pop()
        assert len(first.children) == 2
        third = (tree.leaves - first.children).pop()
        assert third

    def test_ignores_indented_code_blocks(self):
        plan = """
- task1
  ```
  - not a task
  ```
- task2
"""
        tree = parse_tree(plan)
        descriptions = [n.value.description for n in tree.nodes]
        assert "task1" in descriptions
        assert "task2" in descriptions
        assert "not a task" not in descriptions
        assert len(tree.roots) == 2


class TestInferIndent:
    def test_raises_on_mixed_indentation(self):
        plan = "- top\n\t- tab indented\n  - space indented\n"
        with pytest.raises(ValueError, match="mixed indentation"):
            infer_indent(plan)

    def test_returns_consistent_indent(self):
        plan = "- top\n  - child\n  - sibling\n"
        assert infer_indent(plan) == "  "


class TestImports:
    def test_parse_import_does_not_require_pygit2(self):
        """Importing parse and count must not trigger pygit2 import."""
        import importlib
        import sys

        class BlockPygit2:
            def find_spec(self, fullname, _path=None, _target=None):
                if fullname == "pygit2":
                    raise ImportError("pygit2 is intentionally blocked for this test")
                return None

        # Save and clear all mdplan modules to force re-import
        mdplan_keys = [k for k in sys.modules if k.startswith("mdplan")]
        saved_mdplan = {k: sys.modules.pop(k) for k in mdplan_keys}
        saved_pygit2 = sys.modules.pop("pygit2", None)

        blocker = BlockPygit2()
        sys.meta_path.insert(0, blocker)
        try:
            # These imports must succeed without pygit2
            mod = importlib.import_module("mdplan.parse")
            assert hasattr(mod, "parse_tree")
            mod2 = importlib.import_module("mdplan.count")
            assert hasattr(mod2, "count_all_tasks")
        finally:
            sys.meta_path.remove(blocker)
            if saved_pygit2 is not None:
                sys.modules["pygit2"] = saved_pygit2
            sys.modules.update(saved_mdplan)
