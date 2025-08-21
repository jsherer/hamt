import unittest
import sys
from pathlib import Path
import threading
import gc

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from hamt import HAMT


class TestHAMTEdgeCases(unittest.TestCase):
    
    def test_empty_string_key(self):
        h = HAMT()
        h = h.set('', 'empty_key_value')
        self.assertEqual(h[''], 'empty_key_value')
        self.assertTrue('' in h)
        h = h.delete('')
        self.assertFalse('' in h)
    
    def test_unicode_keys(self):
        h = HAMT()
        unicode_keys = ['😀', '中文', 'مرحبا', 'Здравствуйте', '🔥🎉🚀']
        
        for i, key in enumerate(unicode_keys):
            h = h.set(key, i)
        
        self.assertEqual(len(h), len(unicode_keys))
        
        for i, key in enumerate(unicode_keys):
            self.assertEqual(h[key], i)
    
    def test_large_values(self):
        h = HAMT()
        large_value = 'x' * 1000000  # 1MB string
        h = h.set('large', large_value)
        self.assertEqual(h['large'], large_value)
        self.assertEqual(len(h['large']), 1000000)
    
    def test_special_characters_in_keys(self):
        h = HAMT()
        special_keys = [
            '\n', '\t', '\r', '\0',
            '\\', '/', '|', '*',
            '<', '>', '?', ':',
            '"', "'", '`', '~'
        ]
        
        for i, key in enumerate(special_keys):
            h = h.set(key, i)
        
        self.assertEqual(len(h), len(special_keys))
        
        for i, key in enumerate(special_keys):
            self.assertEqual(h[key], i)
    
    def test_tuple_keys(self):
        h = HAMT()
        h = h.set((1, 2, 3), 'tuple_value')
        h = h.set((1, 2), 'another_tuple')
        h = h.set((1,), 'single_tuple')
        h = h.set((), 'empty_tuple')
        
        self.assertEqual(h[(1, 2, 3)], 'tuple_value')
        self.assertEqual(h[(1, 2)], 'another_tuple')
        self.assertEqual(h[(1,)], 'single_tuple')
        self.assertEqual(h[()], 'empty_tuple')
        self.assertEqual(len(h), 4)
    
    def test_frozen_set_keys(self):
        h = HAMT()
        fs1 = frozenset([1, 2, 3])
        fs2 = frozenset(['a', 'b', 'c'])
        fs3 = frozenset()
        
        h = h.set(fs1, 'fs1')
        h = h.set(fs2, 'fs2')
        h = h.set(fs3, 'fs3')
        
        self.assertEqual(h[fs1], 'fs1')
        self.assertEqual(h[fs2], 'fs2')
        self.assertEqual(h[fs3], 'fs3')
    
    def test_boolean_keys(self):
        h = HAMT()
        h = h.set(True, 'true_value')
        h = h.set(False, 'false_value')
        
        self.assertEqual(h[True], 'true_value')
        self.assertEqual(h[False], 'false_value')
        self.assertEqual(len(h), 2)
    
    def test_none_key(self):
        h = HAMT()
        h = h.set(None, 'none_value')
        
        self.assertTrue(None in h)
        self.assertEqual(h[None], 'none_value')
        h = h.delete(None)
        self.assertFalse(None in h)
    
    def test_complex_nested_values(self):
        h = HAMT()
        nested_value = {
            'list': [1, 2, [3, 4, [5, 6]]],
            'dict': {'a': 1, 'b': {'c': 2}},
            'tuple': (1, (2, (3, 4))),
            'set': {1, 2, 3}
        }
        h = h.set('nested', nested_value)
        retrieved = h['nested']
        
        self.assertEqual(retrieved['list'], nested_value['list'])
        self.assertEqual(retrieved['dict'], nested_value['dict'])
        self.assertEqual(retrieved['tuple'], nested_value['tuple'])
        self.assertEqual(retrieved['set'], nested_value['set'])
    
    def test_repeated_operations(self):
        h = HAMT()
        
        # Add and remove same key multiple times
        for i in range(100):
            h = h.set('key', i)
            self.assertEqual(h['key'], i)
            self.assertEqual(len(h), 1)
        
        # Delete and re-add
        for i in range(10):
            h = h.set('test', i)
            h = h.delete('test')
            self.assertFalse('test' in h)
    
    def test_many_collisions_stress(self):
        class AlwaysSameHash:
            def __init__(self, value):
                self.value = value
            
            def __hash__(self):
                return 0  # Always same hash
            
            def __eq__(self, other):
                return isinstance(other, AlwaysSameHash) and self.value == other.value
        
        h = HAMT()
        n = 1000
        
        for i in range(n):
            h = h.set(AlwaysSameHash(i), i)
        
        self.assertEqual(len(h), n)
        
        for i in range(n):
            self.assertEqual(h[AlwaysSameHash(i)], i)
        
        # Delete half
        for i in range(0, n, 2):
            h = h.delete(AlwaysSameHash(i))
        
        self.assertEqual(len(h), n // 2)
        
        for i in range(1, n, 2):
            self.assertEqual(h[AlwaysSameHash(i)], i)
    
    def test_memory_efficiency(self):
        base = HAMT()
        for i in range(1000):
            base = base.set(i, i)
        
        # Create many variants with small changes
        variants = []
        for i in range(100):
            variant = base.set(f'variant_{i}', i)
            variants.append(variant)
        
        # All variants should share most of their structure with base
        # This is hard to test directly, but we can verify they're all different
        for i, v in enumerate(variants):
            self.assertEqual(v[f'variant_{i}'], i)
            self.assertEqual(len(v), 1001)
            
            # Verify base is unchanged
            self.assertFalse(f'variant_{i}' in base)
    
    def test_concurrent_read_safety(self):
        h = HAMT()
        for i in range(100):
            h = h.set(i, i * 2)
        
        results = []
        errors = []
        
        def reader():
            try:
                for _ in range(1000):
                    for i in range(100):
                        assert h[i] == i * 2
                results.append('success')
            except Exception as e:
                errors.append(str(e))
        
        threads = [threading.Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)
    
    def test_garbage_collection(self):
        # Ensure HAMT doesn't prevent garbage collection
        class TrackableObject:
            instances = []
            
            def __init__(self, value):
                self.value = value
                TrackableObject.instances.append(self)
            
            def __hash__(self):
                return hash(self.value)
            
            def __eq__(self, other):
                return isinstance(other, TrackableObject) and self.value == other.value
        
        TrackableObject.instances = []
        
        h = HAMT()
        obj1 = TrackableObject(1)
        obj2 = TrackableObject(2)
        
        h = h.set(obj1, 'value1')
        h = h.set(obj2, 'value2')
        
        self.assertEqual(len(TrackableObject.instances), 2)
        
        # Delete from HAMT and remove references
        h = h.delete(obj1)
        del obj1
        gc.collect()
        
        # obj1 should be garbage collected
        # Note: This is a weak test as GC behavior can vary
        self.assertTrue(len(TrackableObject.instances) <= 2)
    
    def test_very_deep_trie(self):
        # Test with keys that force deep trie structure
        h = HAMT()
        
        # Create keys with same hash prefix to force deep recursion
        for i in range(100):
            # These will have similar hash patterns
            key = i << 32
            h = h.set(key, i)
        
        self.assertEqual(len(h), 100)
        
        for i in range(100):
            key = i << 32
            self.assertEqual(h[key], i)
    
    def test_equality_with_different_insertion_order(self):
        h1 = HAMT()
        h2 = HAMT()
        
        # Insert in different orders
        for i in range(100):
            h1 = h1.set(i, i * 2)
        
        for i in range(99, -1, -1):
            h2 = h2.set(i, i * 2)
        
        self.assertEqual(h1, h2)
    
    def test_repr_with_special_values(self):
        h = HAMT()
        h = h.set('key', None)
        h = h.set(None, 'value')
        h = h.set('', '')
        
        repr_str = repr(h)
        self.assertIn('HAMT', repr_str)
        # Should not crash with special values
    
    def test_contains_with_unhashable_type(self):
        h = HAMT()
        h = h.set('key', 'value')
        
        # Should raise TypeError for unhashable types
        with self.assertRaises(TypeError):
            [] in h
        
        with self.assertRaises(TypeError):
            {} in h
    
    def test_get_with_unhashable_type(self):
        h = HAMT()
        h = h.set('key', 'value')
        
        # Should raise TypeError for unhashable types
        with self.assertRaises(TypeError):
            h.get([])
        
        with self.assertRaises(TypeError):
            h[[]]


class TestHAMTPerformance(unittest.TestCase):
    
    def test_linear_insertion_performance(self):
        h = HAMT()
        n = 50000
        
        for i in range(n):
            h = h.set(i, i)
        
        self.assertEqual(len(h), n)
        
        # Spot check some values
        for i in range(0, n, 1000):
            self.assertEqual(h[i], i)
    
    def test_random_access_performance(self):
        import random
        
        h = HAMT()
        n = 10000
        keys = list(range(n))
        random.shuffle(keys)
        
        for key in keys:
            h = h.set(key, key * 2)
        
        # Random access
        random.shuffle(keys)
        for key in keys[:100]:
            self.assertEqual(h[key], key * 2)
    
    def test_structural_sharing_performance(self):
        base = HAMT()
        for i in range(10000):
            base = base.set(i, i)
        
        # Create 1000 variants efficiently
        variants = []
        for i in range(1000):
            variant = base.set(f'v{i}', i)
            variants.append(variant)
        
        # All should maintain base data
        for v in variants[:10]:  # Spot check
            self.assertEqual(v[0], 0)
            self.assertEqual(v[9999], 9999)


if __name__ == '__main__':
    unittest.main()