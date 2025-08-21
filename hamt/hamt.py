class HAMTNode:
    __slots__ = ()
    
    def find(self, shift, hash_val, key):
        raise NotImplementedError
    
    def assoc(self, shift, hash_val, key, value):
        raise NotImplementedError
    
    def without(self, shift, hash_val, key):
        raise NotImplementedError


class BitmapNode(HAMTNode):
    __slots__ = ('_bitmap', '_array')
    
    def __init__(self, bitmap, array):
        self._bitmap = bitmap
        self._array = array
    
    def find(self, shift, hash_val, key):
        bit = 1 << ((hash_val >> shift) & 0x1f)
        if not (self._bitmap & bit):
            raise KeyError(key)
        
        idx = _popcount(self._bitmap & (bit - 1))
        node_or_val = self._array[idx * 2]
        
        if node_or_val is None:
            key_or_null = self._array[idx * 2]
            val_or_node = self._array[idx * 2 + 1]
            if key_or_null == key:
                return val_or_node
            raise KeyError(key)
        
        if isinstance(node_or_val, HAMTNode):
            return node_or_val.find(shift + 5, hash_val, key)
        
        if node_or_val == key:
            return self._array[idx * 2 + 1]
        raise KeyError(key)
    
    def assoc(self, shift, hash_val, key, value):
        bit = 1 << ((hash_val >> shift) & 0x1f)
        idx = _popcount(self._bitmap & (bit - 1))
        
        if self._bitmap & bit:
            key_or_node = self._array[idx * 2]
            val_or_node = self._array[idx * 2 + 1]
            
            if key_or_node is None and val_or_node is None:
                return self
            
            if isinstance(key_or_node, HAMTNode):
                new_node = key_or_node.assoc(shift + 5, hash_val, key, value)
                if new_node is key_or_node:
                    return self
                new_array = self._array[:]
                new_array[idx * 2] = new_node
                return BitmapNode(self._bitmap, new_array)
            
            if key_or_node == key:
                if val_or_node is value:
                    return self
                new_array = self._array[:]
                new_array[idx * 2 + 1] = value
                return BitmapNode(self._bitmap, new_array)
            
            if shift >= 25:
                new_node = CollisionNode([key_or_node, val_or_node, key, value])
            else:
                existing_hash = hash(key_or_node)
                new_node = _create_node(shift + 5, key_or_node, val_or_node, 
                                       hash_val, key, value)
            
            new_array = self._array[:]
            new_array[idx * 2] = new_node
            new_array[idx * 2 + 1] = None
            return BitmapNode(self._bitmap, new_array)
        else:
            n = _popcount(self._bitmap)
            new_array = [None] * (2 * (n + 1))
            new_array[:idx * 2] = self._array[:idx * 2]
            new_array[idx * 2] = key
            new_array[idx * 2 + 1] = value
            new_array[idx * 2 + 2:] = self._array[idx * 2:]
            return BitmapNode(self._bitmap | bit, new_array)
    
    def without(self, shift, hash_val, key):
        bit = 1 << ((hash_val >> shift) & 0x1f)
        if not (self._bitmap & bit):
            raise KeyError(key)
        
        idx = _popcount(self._bitmap & (bit - 1))
        key_or_node = self._array[idx * 2]
        val_or_node = self._array[idx * 2 + 1]
        
        if isinstance(key_or_node, HAMTNode):
            new_node = key_or_node.without(shift + 5, hash_val, key)
            if new_node is key_or_node:
                return self
            
            if new_node is None:
                if _popcount(self._bitmap) == 1:
                    return None
                new_array = self._array[:idx * 2] + self._array[idx * 2 + 2:]
                return BitmapNode(self._bitmap & ~bit, new_array)
            
            new_array = self._array[:]
            new_array[idx * 2] = new_node
            return BitmapNode(self._bitmap, new_array)
        
        if key_or_node != key:
            raise KeyError(key)
        
        if _popcount(self._bitmap) == 1:
            return None
        
        new_array = self._array[:idx * 2] + self._array[idx * 2 + 2:]
        return BitmapNode(self._bitmap & ~bit, new_array)
    
    def __iter__(self):
        for i in range(0, len(self._array), 2):
            key_or_node = self._array[i]
            val_or_node = self._array[i + 1]
            
            if isinstance(key_or_node, HAMTNode):
                yield from key_or_node
            elif key_or_node is not None:
                yield key_or_node


class CollisionNode(HAMTNode):
    __slots__ = ('_items',)
    
    def __init__(self, items):
        self._items = items
    
    def find(self, shift, hash_val, key):
        for i in range(0, len(self._items), 2):
            if self._items[i] == key:
                return self._items[i + 1]
        raise KeyError(key)
    
    def assoc(self, shift, hash_val, key, value):
        for i in range(0, len(self._items), 2):
            if self._items[i] == key:
                if self._items[i + 1] is value:
                    return self
                new_items = self._items[:]
                new_items[i + 1] = value
                return CollisionNode(new_items)
        
        new_items = self._items + [key, value]
        return CollisionNode(new_items)
    
    def without(self, shift, hash_val, key):
        for i in range(0, len(self._items), 2):
            if self._items[i] == key:
                new_items = self._items[:i] + self._items[i + 2:]
                if len(new_items) == 2:
                    return None
                return CollisionNode(new_items)
        raise KeyError(key)
    
    def __iter__(self):
        for i in range(0, len(self._items), 2):
            yield self._items[i]


def _popcount(x):
    x = x - ((x >> 1) & 0x55555555)
    x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
    x = (x + (x >> 4)) & 0x0f0f0f0f
    x = x + (x >> 8)
    x = x + (x >> 16)
    return x & 0x3f


def _create_node(shift, key1, val1, hash2, key2, val2):
    hash1 = hash(key1)
    
    if shift > 25:
        return CollisionNode([key1, val1, key2, val2])
    
    mask1 = (hash1 >> shift) & 0x1f
    mask2 = (hash2 >> shift) & 0x1f
    
    if mask1 == mask2:
        node = _create_node(shift + 5, key1, val1, hash2, key2, val2)
        bitmap = 1 << mask1
        return BitmapNode(bitmap, [node, None])
    else:
        bitmap = (1 << mask1) | (1 << mask2)
        if mask1 < mask2:
            return BitmapNode(bitmap, [key1, val1, key2, val2])
        else:
            return BitmapNode(bitmap, [key2, val2, key1, val1])


class HAMT:
    __slots__ = ('_root', '_size')
    
    def __init__(self, items=None):
        self._root = None
        self._size = 0
        
        if items:
            if hasattr(items, 'items'):
                items = items.items()
            
            for key, value in items:
                self._root, added = self._assoc_with_added(self._root, 0, hash(key), key, value)
                if added:
                    self._size += 1
    
    def _assoc_with_added(self, node, shift, hash_val, key, value):
        if node is None:
            return BitmapNode(1 << ((hash_val >> shift) & 0x1f), [key, value]), True
        
        try:
            existing = node.find(shift, hash_val, key)
            new_node = node.assoc(shift, hash_val, key, value)
            return new_node, False
        except KeyError:
            new_node = node.assoc(shift, hash_val, key, value)
            return new_node, True
    
    def get(self, key, default=None):
        if self._root is None:
            return default
        try:
            return self._root.find(0, hash(key), key)
        except KeyError:
            return default
    
    def __getitem__(self, key):
        if self._root is None:
            raise KeyError(key)
        return self._root.find(0, hash(key), key)
    
    def set(self, key, value):
        new_hamt = HAMT()
        if self._root is None:
            new_hamt._root = BitmapNode(1 << (hash(key) & 0x1f), [key, value])
            new_hamt._size = 1
        else:
            new_hamt._root, added = self._assoc_with_added(self._root, 0, hash(key), key, value)
            new_hamt._size = self._size + (1 if added else 0)
        return new_hamt
    
    def delete(self, key):
        if self._root is None:
            raise KeyError(key)
        
        new_root = self._root.without(0, hash(key), key)
        new_hamt = HAMT()
        new_hamt._root = new_root
        new_hamt._size = self._size - 1
        return new_hamt
    
    def __contains__(self, key):
        if self._root is None:
            return False
        try:
            self._root.find(0, hash(key), key)
            return True
        except KeyError:
            return False
    
    def __len__(self):
        return self._size
    
    def __iter__(self):
        if self._root is not None:
            yield from self._root
    
    def keys(self):
        return list(self)
    
    def values(self):
        return [self[k] for k in self]
    
    def items(self):
        return [(k, self[k]) for k in self]
    
    def __repr__(self):
        if self._size == 0:
            return 'HAMT({})'
        items = ', '.join(f'{k!r}: {v!r}' for k, v in self.items())
        return f'HAMT({{{items}}})'
    
    def __eq__(self, other):
        if not isinstance(other, HAMT):
            return False
        if len(self) != len(other):
            return False
        for key in self:
            if key not in other or self[key] != other[key]:
                return False
        return True