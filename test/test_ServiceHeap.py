from unittest import TestCase

import collections

from rosilluminant.multireg import ServiceHeap, ServiceRecord


class TestServiceHeap(TestCase):
    def setUp(self):
        self.services = ['s0', 's1']
        self.addresses = list(range(10)) + list(range(10))

    def fullfill(self):
        heap = ServiceHeap()
        for s in self.services:
            for a in self.addresses:
                heap.insert(s, a)
        return heap

    def test_record(self):
        s0 = ServiceRecord('s0', 1)
        s1 = ServiceRecord('s1', 2)
        s2 = ServiceRecord('s0', 1)
        s1.count(1)
        s2.count(2)
        self.assertFalse(s0 == s1)
        self.assertTrue(s0 == s2)
        self.assertTrue(s0 < s1 < s2)

    def test_insert(self):
        heap = self.fullfill()
        self.assertEqual(len(heap.heap), 20)

    def test_lru(self):
        heap = self.fullfill()
        times = len(heap)
        counter = collections.defaultdict(int)
        for _ in range(times):
            results = [heap.minimal_update() for _ in range(10)]
            diff = len(results) == len(set(results))
            self.assertTrue(diff)
            for r in results:
                counter[r] += 1
        self.assertTrue(all(map(lambda x: x == 10, counter.values())))
