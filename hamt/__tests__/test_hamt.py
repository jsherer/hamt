import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from hamt import HAMT


class TestHAMT(unittest.TestCase):
    
    def test_empty_hamt(self):
        h = HAMT()
        self.assertEqual(len(h), 0)
        self.assertFalse('key' in h)
        self.assertEqual(list(h), [])
        with self.assertRaises(KeyError):
            h['key']
    
    def test_single_item(self):
        h = HAMT()
        h2 = h.set('key', 'value')
        
        self.assertEqual(len(h), 0)
        self.assertEqual(len(h2), 1)
        self.assertTrue('key' in h2)
        self.assertEqual(h2['key'], 'value')
        self.assertEqual(h2.get('key'), 'value')
        self.assertEqual(list(h2), ['key'])
    
    def test_multiple_items(self):
        h = HAMT()
        h = h.set('a', 1)
        h = h.set('b', 2)
        h = h.set('c', 3)
        
        self.assertEqual(len(h), 3)
        self.assertEqual(h['a'], 1)
        self.assertEqual(h['b'], 2)
        self.assertEqual(h['c'], 3)
        self.assertEqual(set(h.keys()), {'a', 'b', 'c'})
        self.assertEqual(set(h.values()), {1, 2, 3})
        self.assertEqual(set(h.items()), {('a', 1), ('b', 2), ('c', 3)})
    
    def test_update_value(self):
        h = HAMT()
        h1 = h.set('key', 'value1')
        h2 = h1.set('key', 'value2')
        
        self.assertEqual(len(h1), 1)
        self.assertEqual(len(h2), 1)
        self.assertEqual(h1['key'], 'value1')
        self.assertEqual(h2['key'], 'value2')
    
    def test_delete(self):
        h = HAMT()
        h = h.set('a', 1)
        h = h.set('b', 2)
        h = h.set('c', 3)
        
        h2 = h.delete('b')
        
        self.assertEqual(len(h), 3)
        self.assertEqual(len(h2), 2)
        self.assertTrue('b' in h)
        self.assertFalse('b' in h2)
        self.assertEqual(set(h2.keys()), {'a', 'c'})
        
        with self.assertRaises(KeyError):
            h2.delete('b')
    
    def test_immutability(self):
        h1 = HAMT()
        h2 = h1.set('a', 1)
        h3 = h2.set('b', 2)
        h4 = h3.set('c', 3)
        h5 = h4.delete('b')
        
        self.assertEqual(len(h1), 0)
        self.assertEqual(len(h2), 1)
        self.assertEqual(len(h3), 2)
        self.assertEqual(len(h4), 3)
        self.assertEqual(len(h5), 2)
        
        self.assertFalse('a' in h1)
        self.assertTrue('a' in h2)
        self.assertTrue('a' in h3)
        self.assertTrue('a' in h4)
        self.assertTrue('a' in h5)
        
        self.assertFalse('b' in h1)
        self.assertFalse('b' in h2)
        self.assertTrue('b' in h3)
        self.assertTrue('b' in h4)
        self.assertFalse('b' in h5)
    
    def test_hash_collision(self):
        class BadHash:
            def __init__(self, value):
                self.value = value
            
            def __hash__(self):
                return 42
            
            def __eq__(self, other):
                return isinstance(other, BadHash) and self.value == other.value
            
            def __repr__(self):
                return f'BadHash({self.value})'
        
        h = HAMT()
        h = h.set(BadHash(1), 'value1')
        h = h.set(BadHash(2), 'value2')
        h = h.set(BadHash(3), 'value3')
        
        self.assertEqual(len(h), 3)
        self.assertEqual(h[BadHash(1)], 'value1')
        self.assertEqual(h[BadHash(2)], 'value2')
        self.assertEqual(h[BadHash(3)], 'value3')
        
        h2 = h.delete(BadHash(2))
        self.assertEqual(len(h2), 2)
        self.assertFalse(BadHash(2) in h2)
        self.assertTrue(BadHash(1) in h2)
        self.assertTrue(BadHash(3) in h2)
    
    def test_large_dataset(self):
        h = HAMT()
        n = 10000
        
        for i in range(n):
            h = h.set(f'key{i}', i)
        
        self.assertEqual(len(h), n)
        
        for i in range(n):
            self.assertEqual(h[f'key{i}'], i)
        
        for i in range(0, n, 2):
            h = h.delete(f'key{i}')
        
        self.assertEqual(len(h), n // 2)
        
        for i in range(1, n, 2):
            self.assertEqual(h[f'key{i}'], i)
        
        for i in range(0, n, 2):
            self.assertFalse(f'key{i}' in h)
    
    def test_init_with_dict(self):
        d = {'a': 1, 'b': 2, 'c': 3}
        h = HAMT(d)
        
        self.assertEqual(len(h), 3)
        self.assertEqual(h['a'], 1)
        self.assertEqual(h['b'], 2)
        self.assertEqual(h['c'], 3)
    
    def test_init_with_items(self):
        items = [('a', 1), ('b', 2), ('c', 3)]
        h = HAMT(items)
        
        self.assertEqual(len(h), 3)
        self.assertEqual(h['a'], 1)
        self.assertEqual(h['b'], 2)
        self.assertEqual(h['c'], 3)
    
    def test_get_with_default(self):
        h = HAMT()
        h = h.set('key', 'value')
        
        self.assertEqual(h.get('key'), 'value')
        self.assertEqual(h.get('missing'), None)
        self.assertEqual(h.get('missing', 'default'), 'default')
    
    def test_equality(self):
        h1 = HAMT()
        h1 = h1.set('a', 1)
        h1 = h1.set('b', 2)
        
        h2 = HAMT()
        h2 = h2.set('b', 2)
        h2 = h2.set('a', 1)
        
        h3 = HAMT()
        h3 = h3.set('a', 1)
        h3 = h3.set('b', 3)
        
        h4 = HAMT()
        h4 = h4.set('a', 1)
        
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)
        self.assertNotEqual(h1, h4)
        self.assertNotEqual(h1, {'a': 1, 'b': 2})
    
    def test_repr(self):
        h = HAMT()
        self.assertEqual(repr(h), 'HAMT({})')
        
        h = h.set('a', 1)
        self.assertIn('a', repr(h))
        self.assertIn('1', repr(h))
    
    def test_none_values(self):
        h = HAMT()
        h = h.set('key', None)
        
        self.assertEqual(len(h), 1)
        self.assertTrue('key' in h)
        self.assertIsNone(h['key'])
        self.assertIsNone(h.get('key'))
        self.assertIsNone(h.get('key', 'default'))
    
    def test_numeric_keys(self):
        h = HAMT()
        
        for i in range(100):
            h = h.set(i, i * 2)
        
        self.assertEqual(len(h), 100)
        
        for i in range(100):
            self.assertEqual(h[i], i * 2)
    
    def test_mixed_types(self):
        h = HAMT()
        h = h.set('string', 1)
        h = h.set(42, 2)
        h = h.set((1, 2), 3)
        h = h.set(3.14, 4)
        
        self.assertEqual(len(h), 4)
        self.assertEqual(h['string'], 1)
        self.assertEqual(h[42], 2)
        self.assertEqual(h[(1, 2)], 3)
        self.assertEqual(h[3.14], 4)


if __name__ == '__main__':
    unittest.main()