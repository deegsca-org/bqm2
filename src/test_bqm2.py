import unittest
from collections import defaultdict

from bqm2 import DependencyExecutor, find_cycles


class Test(unittest.TestCase):
    def testHandleRetries(self):
        de = DependencyExecutor(set([]), {}, maxRetry=1)
        retries = defaultdict(lambda: 1)
        de.handleRetries(retries, "aKey")

        # do it again which should blow up
        try:
            de.handleRetries(retries, "aKey")
            self.fail("Should have thrown exception")
        except:
            pass


def test_find_cycles_cycle_to_self():
    assert set(['a']) == find_cycles({'a': set('a')})


def test_find_cycles_no_cycle():
    assert set([]) == find_cycles({'a': set('b'), 'b': set()})


def test_find_cycles_cycle_distance_two():
    assert set(['a', 'b', 'c']) == find_cycles({
        'a': set('b'),
        'b': set('c'),
        'c': set('a'),
        'd': set()}
    )
