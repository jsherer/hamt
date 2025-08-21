# HAMT - Hash Array Mapped Trie

A pure Python implementation of a Hash Array Mapped Trie (HAMT), providing an immutable, persistent mapping data structure with efficient updates and structural sharing.

**Key Advantage**: While HAMT is slower than dict for single operations, it's **14x faster and uses 99.8% less memory** than dict.copy() when creating multiple variants, making it ideal for functional programming and version management.

## What is HAMT?

HAMT (Hash Array Mapped Trie) is a data structure that combines the benefits of hash tables and tries to create an efficient immutable mapping. It was popularized by languages like Clojure and Scala for implementing persistent data structures.

### Key Features

- **Immutability**: All operations return new instances, original remains unchanged
- **Persistence**: Old versions remain available after updates
- **Structural Sharing**: New versions share unchanged parts with old versions
- **O(log32 n) Operations**: Effectively constant time for practical data sizes
- **Thread-Safe**: Immutability makes it inherently safe for concurrent access
- **Memory Efficient**: When creating many similar versions

## Installation

### Prerequisites

- Python 3.11 or higher
- Virtual environment (recommended)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd hamt
```

2. Create and activate virtual environment:
```bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
make install
```

## Usage

### Basic Operations

```python
from hamt import HAMT

# Create an empty HAMT
h = HAMT()

# Add key-value pairs (returns new instance)
h1 = h.set('key1', 'value1')
h2 = h1.set('key2', 'value2')

# Original remains unchanged
assert len(h) == 0
assert len(h1) == 1
assert len(h2) == 2

# Access values
value = h2['key1']  # 'value1'
value = h2.get('key3', 'default')  # 'default'

# Check membership
if 'key1' in h2:
    print("Key exists")

# Delete keys (returns new instance)
h3 = h2.delete('key1')
assert 'key1' not in h3
assert 'key1' in h2  # Original unchanged

# Iteration
for key in h2:
    print(key, h2[key])

# Get all keys, values, items
keys = h2.keys()
values = h2.values()
items = h2.items()
```

### Initialize from Existing Data

```python
# From dictionary
d = {'a': 1, 'b': 2, 'c': 3}
h = HAMT(d)

# From list of tuples
items = [('a', 1), ('b', 2), ('c', 3)]
h = HAMT(items)
```

### Advanced Usage: Structural Sharing

```python
# Traditional dict approach - full copies
base_dict = {'a': 1, 'b': 2, 'c': 3, ...}  # 10,000 items
variants = []
for i in range(500):
    variant = base_dict.copy()  # Full copy every time!
    variant[f'item_{i}'] = i
    variants.append(variant)
# Result: 500 full copies, ~140MB memory, 42ms

# HAMT approach - structural sharing
base_hamt = HAMT({'a': 1, 'b': 2, 'c': 3, ...})  # 10,000 items
variants = []
for i in range(500):
    variant = base_hamt.set(f'item_{i}', i)  # Shares 99.9% of structure!
    variants.append(variant)
# Result: 500 variants sharing structure, ~0.3MB memory, 3ms

# The magic: each variant only stores the differences
# All unchanged nodes are shared between versions
```

This structural sharing makes HAMT ideal for:
- Implementing undo/redo with full state snapshots
- Creating "what-if" scenarios without duplicating data
- Building version control systems for data structures
- Maintaining audit trails with complete state history

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with verbose output
make test-verbose

# Run with coverage report
make test-coverage
```

### Running Benchmarks

```bash
# Small benchmark (1K operations, ~1 second)
make benchmark-small

# Medium benchmark (10K operations, ~5 seconds) - Default
make benchmark

# Large benchmark (100K operations, ~30 seconds)
make benchmark-large
```

The benchmarks test:
- **Insertions**: Adding key-value pairs
- **Lookups**: Reading values by key
- **Deletions**: Removing key-value pairs
- **Iteration**: Traversing all keys
- **Structural sharing vs Copying**: Comparing HAMT variants vs dict.copy()
- **Hash collisions**: Performance with colliding hash values

Benchmark sizes:
- **Small**: 1,000 insertions, 500 deletions, 10 variants
- **Medium**: 10,000 insertions, 5,000 deletions, 100 variants  
- **Large**: 100,000 insertions, 25,000 deletions, 500 variants

#### Key Benchmark Results

From the large benchmark (100K items, 500 variants):
```
Single Operations:
  Insertions: dict 0.02s vs HAMT 0.69s (36x slower)
  Lookups:    dict 0.01s vs HAMT 0.12s (11x slower)
  
Creating Variants:
  dict.copy(): 42ms total, 140MB memory
  HAMT:        3ms total, 0.3MB memory
  → HAMT is 14x faster and uses 99.8% less memory
```

### Code Quality

```bash
# Format code
make format

# Check formatting and linting
make lint

# Clean build artifacts
make clean
```

## Performance Characteristics

### Time Complexity

| Operation | Average Case | Worst Case |
|-----------|-------------|------------|
| get       | O(log32 n)  | O(log32 n) |
| set       | O(log32 n)  | O(log32 n) |
| delete    | O(log32 n)  | O(log32 n) |
| contains  | O(log32 n)  | O(log32 n) |
| len       | O(1)        | O(1)       |

Note: log32 n is effectively constant for practical data sizes (log32 of 1 billion H 6)

### Space Complexity

- **Single HAMT**: O(n) where n is the number of key-value pairs
- **Multiple versions**: Efficient due to structural sharing
- **Creating k versions with m changes each**: O(n + k�m) instead of O(k�n)

### Performance vs dict

Based on our comprehensive benchmarks:

#### Single Operations
- **Insertions**: 25-40x slower than dict
- **Lookups**: 10-25x slower than dict  
- **Deletions**: 25-40x slower than dict
- **Iteration**: 10-20x slower than dict

#### Creating Variants (The HAMT Advantage)
When creating multiple versions with small changes:
- **Speed**: HAMT is **2.7-14x faster** than dict.copy()
- **Memory**: HAMT uses **~99.8% less memory** through structural sharing
- **Example**: Creating 500 variants of a 10,000 item collection:
  - Dict approach: 42ms, ~140MB memory
  - HAMT approach: 3ms, ~0.3MB memory (shares 99.9% of structure)

## When to Use HAMT

### Use HAMT when you need:

- **Immutable data structures** for functional programming
- **Version history** - keeping multiple versions of data
- **Thread safety** without locks
- **Undo/redo functionality** in applications
- **Structural sharing** for memory efficiency
- **Creating many variants** of a base data structure
- **Copy-on-write semantics** with better performance than dict.copy()

### Use Python dict when you need:

- Maximum performance for single-threaded operations
- Mutable in-place operations
- Simple key-value storage without versioning
- Best performance for single instances without copying

### Real-world Use Cases

HAMT excels in scenarios like:
- **Configuration management**: Track config changes across deployments
- **State management**: Redux-style state trees in Python applications
- **Caching with history**: Keep previous cache states for rollback
- **Parallel processing**: Safe concurrent access without locks
- **Event sourcing**: Efficient storage of incremental state changes

## Implementation Details

This HAMT implementation uses:

- **32-way branching factor** for the trie nodes
- **Bitmap indexing** for sparse arrays
- **Collision nodes** for hash collisions
- **Path copying** for persistence

The trie structure uses 5 bits of the hash at each level, creating up to 32 branches per node. This provides a good balance between tree depth and node size.

## API Reference

### HAMT Class

#### `__init__(items=None)`
Create a new HAMT, optionally initialized with items.

#### `set(key, value) -> HAMT`
Return a new HAMT with the key-value pair added/updated.

#### `get(key, default=None)`
Get value for key, return default if not found.

#### `__getitem__(key)`
Get value for key, raise KeyError if not found.

#### `delete(key) -> HAMT`
Return a new HAMT with the key removed.

#### `__contains__(key) -> bool`
Check if key exists in the HAMT.

#### `__len__() -> int`
Return the number of key-value pairs.

#### `__iter__()`
Iterate over keys.

#### `keys() -> list`
Return list of all keys.

#### `values() -> list`
Return list of all values.

#### `items() -> list`
Return list of (key, value) tuples.

#### `__eq__(other) -> bool`
Check equality with another HAMT.

#### `__repr__() -> str`
Return string representation of the HAMT.

## Testing

The test suite includes:

- Basic functionality tests
- Edge cases (empty keys, special characters, Unicode)
- Hash collision handling
- Large dataset tests
- Concurrency tests
- Memory efficiency tests
- Performance tests

Run tests with `make test-verbose` to see all test cases.

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass (`make test`)
2. Code is formatted (`make format`)
3. New features include tests
4. Documentation is updated

## License

See [LICENSE](LICENSE)

## Acknowledgments

The HAMT data structure was originally described by Phil Bagwell in "Ideal Hash Trees" (2001). This implementation is inspired by Clojure's PersistentHashMap and Python's built-in HAMT (used in contextvars).

## Further Reading

- [Ideal Hash Trees by Phil Bagwell](https://infoscience.epfl.ch/record/64398/files/idealhashtrees.pdf)
- [Understanding Clojure's Persistent Vectors](https://hypirion.com/musings/understanding-persistent-vector-pt-1)
- [Python's HAMT Implementation](https://github.com/python/cpython/blob/main/Python/hamt.c)
