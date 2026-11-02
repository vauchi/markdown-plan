from ..count import count_all_tasks, count_remaining_tasks, count_tasks


def test_counts_a_flat_list():
    plan = """1. first task
2. second"""
    num = count_remaining_tasks(plan)

    assert num == 2


def test_only_counts_leaves_as_remaining_tasks():
    plan = """
1. create plan
    - this is one step
    - here is another
2. edit plan
    - something
"""
    num = count_remaining_tasks(plan)

    assert num == 3, "should not count the parent tasks"


def test_does_not_count_completed_tasks():
    plan = """
1. [x] this is done
2. remaining work
"""
    num = count_remaining_tasks(plan)

    assert num == 1


def test_does_not_count_subtasks_of_finished_parent():
    plan = """
1. [x] parent
  - sub1
  - sub2"""
    num = count_remaining_tasks(plan)

    assert num == 0


def test_counts_all_tasks():
    plan = """
1. [x] first thing
    - do this
    - then that
2. finall, do this"""
    num = count_all_tasks(plan)

    assert num == 3


class TestCountTasks:
    def test_returns_total_and_done_and_remaining(self):
        plan = """
- [x] done1
- [x] done2
- [ ] todo1
"""
        result = count_tasks(plan)
        assert result.total == 3
        assert result.done == 2
        assert result.remaining == 1

    def test_trickles_completion(self):
        plan = """
- [x] parent
  - [ ] child1
  - [ ] child2
"""
        result = count_tasks(plan)
        assert result.total == 2
        assert result.done == 2
        assert result.remaining == 0
