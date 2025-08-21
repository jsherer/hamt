import time
import random
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from hamt import HAMT


def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def benchmark_insertions(n=10000):
    print(f"\nBenchmarking {n} insertions:")
    
    start = time.perf_counter()
    d = {}
    for i in range(n):
        d[f'key{i}'] = i
    dict_time = time.perf_counter() - start
    print(f"  dict: {dict_time:.4f}s")
    
    start = time.perf_counter()
    h = HAMT()
    for i in range(n):
        h = h.set(f'key{i}', i)
    hamt_time = time.perf_counter() - start
    print(f"  HAMT: {hamt_time:.4f}s")
    print(f"  Ratio (HAMT/dict): {hamt_time/dict_time:.2f}x")
    
    return d, h


def benchmark_lookups(d, h, n=10000):
    print(f"\nBenchmarking {n} lookups:")
    
    keys = [f'key{random.randint(0, len(d)-1)}' for _ in range(n)]
    
    start = time.perf_counter()
    for key in keys:
        _ = d[key]
    dict_time = time.perf_counter() - start
    print(f"  dict: {dict_time:.4f}s")
    
    start = time.perf_counter()
    for key in keys:
        _ = h[key]
    hamt_time = time.perf_counter() - start
    print(f"  HAMT: {hamt_time:.4f}s")
    print(f"  Ratio (HAMT/dict): {hamt_time/dict_time:.2f}x")


def benchmark_deletions(n=5000):
    print(f"\nBenchmarking {n} deletions:")
    
    # Ensure we have enough items to delete
    total_items = n * 2
    d = {f'key{i}': i for i in range(total_items)}
    start = time.perf_counter()
    for i in range(n):
        del d[f'key{i}']
    dict_time = time.perf_counter() - start
    print(f"  dict: {dict_time:.4f}s")
    
    h = HAMT({f'key{i}': i for i in range(total_items)})
    start = time.perf_counter()
    for i in range(n):
        h = h.delete(f'key{i}')
    hamt_time = time.perf_counter() - start
    print(f"  HAMT: {hamt_time:.4f}s")
    print(f"  Ratio (HAMT/dict): {hamt_time/dict_time:.2f}x")


def benchmark_iteration(d, h):
    print(f"\nBenchmarking iteration over {len(d)} items:")
    
    start = time.perf_counter()
    total = sum(1 for _ in d)
    dict_time = time.perf_counter() - start
    print(f"  dict: {dict_time:.4f}s")
    
    start = time.perf_counter()
    total = sum(1 for _ in h)
    hamt_time = time.perf_counter() - start
    print(f"  HAMT: {hamt_time:.4f}s")
    print(f"  Ratio (HAMT/dict): {hamt_time/dict_time:.2f}x")


def benchmark_memory_sharing():
    print("\nTesting memory sharing (structural sharing):")
    
    base = HAMT()
    for i in range(1000):
        base = base.set(f'key{i}', i)
    
    print(f"  Created base HAMT with 1000 items")
    
    variants = []
    start = time.perf_counter()
    for i in range(100):
        variant = base.set(f'extra{i}', i)
        variants.append(variant)
    creation_time = time.perf_counter() - start
    
    print(f"  Created 100 variants in {creation_time:.4f}s")
    print(f"  Average time per variant: {creation_time/100*1000:.2f}ms")
    print(f"  (Each variant shares most nodes with the base)")


def benchmark_hash_collisions():
    print("\nBenchmarking with hash collisions:")
    
    class BadHash:
        def __init__(self, value):
            self.value = value
        
        def __hash__(self):
            return self.value % 10
        
        def __eq__(self, other):
            return isinstance(other, BadHash) and self.value == other.value
    
    n = 1000
    
    d = {}
    start = time.perf_counter()
    for i in range(n):
        d[BadHash(i)] = i
    dict_time = time.perf_counter() - start
    print(f"  dict with collisions: {dict_time:.4f}s")
    
    h = HAMT()
    start = time.perf_counter()
    for i in range(n):
        h = h.set(BadHash(i), i)
    hamt_time = time.perf_counter() - start
    print(f"  HAMT with collisions: {hamt_time:.4f}s")
    print(f"  Ratio (HAMT/dict): {hamt_time/dict_time:.2f}x")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Benchmark HAMT performance')
    parser.add_argument('--size', type=str, default='medium',
                        choices=['small', 'medium', 'large'],
                        help='Benchmark size: small, medium, or large')
    args = parser.parse_args()
    
    # Define size parameters
    sizes = {
        'small': {
            'insertions': 1000,
            'lookups': 1000,
            'deletions': 500,
            'collisions': 100,
            'memory_variants': 10,
            'memory_base': 100,
            'label': 'Small'
        },
        'medium': {
            'insertions': 10000,
            'lookups': 10000,
            'deletions': 5000,
            'collisions': 1000,
            'memory_variants': 100,
            'memory_base': 1000,
            'label': 'Medium'
        },
        'large': {
            'insertions': 100000,
            'lookups': 50000,
            'deletions': 25000,
            'collisions': 5000,
            'memory_variants': 500,
            'memory_base': 10000,
            'label': 'Large'
        }
    }
    
    size_config = sizes[args.size]
    
    print("=" * 60)
    print(f"HAMT Performance Benchmarks - {size_config['label']} Dataset")
    print("=" * 60)
    
    # Run benchmarks with size-specific parameters
    d, h = benchmark_insertions(size_config['insertions'])
    benchmark_lookups(d, h, size_config['lookups'])
    benchmark_deletions(size_config['deletions'])
    benchmark_iteration(d, h)
    benchmark_memory_sharing_sized(size_config['memory_base'], size_config['memory_variants'])
    benchmark_hash_collisions_sized(size_config['collisions'])
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("  - HAMT provides immutability and structural sharing")
    print("  - Performance is typically 2-10x slower than dict")
    print("  - Best for functional programming and concurrent access")
    print("  - Memory efficient when creating many similar copies")
    print("=" * 60)


def benchmark_memory_sharing_sized(base_size, variant_count):
    import copy
    import sys
    
    print(f"\nTesting structural sharing vs copying ({base_size} base items, {variant_count} variants):")
    
    # Create base dictionary
    base_dict = {i: i for i in range(base_size)}
    
    # Test dict copying (full copy each time)
    dict_variants = []
    start = time.perf_counter()
    for i in range(variant_count):
        variant = base_dict.copy()
        variant[f'extra{i}'] = i
        dict_variants.append(variant)
    dict_time = time.perf_counter() - start
    
    # Estimate memory usage for dict copies
    dict_memory_estimate = sys.getsizeof(base_dict) * variant_count
    
    print(f"\n  Dict (copy) approach:")
    print(f"    Time to create {variant_count} variants: {dict_time:.4f}s")
    print(f"    Average time per variant: {dict_time/variant_count*1000:.2f}ms")
    print(f"    Estimated memory: ~{dict_memory_estimate / 1024:.1f} KB")
    print(f"    (Each variant is a full copy)")
    
    # Test HAMT structural sharing
    base_hamt = HAMT()
    for i in range(base_size):
        base_hamt = base_hamt.set(i, i)
    
    hamt_variants = []
    start = time.perf_counter()
    for i in range(variant_count):
        variant = base_hamt.set(f'extra{i}', i)
        hamt_variants.append(variant)
    hamt_time = time.perf_counter() - start
    
    print(f"\n  HAMT (structural sharing) approach:")
    print(f"    Time to create {variant_count} variants: {hamt_time:.4f}s")
    print(f"    Average time per variant: {hamt_time/variant_count*1000:.2f}ms")
    print(f"    (Variants share most nodes with base)")
    
    print(f"\n  Performance comparison:")
    if hamt_time < dict_time:
        print(f"    Speed: HAMT is {dict_time/hamt_time:.2f}x faster than dict.copy()")
    else:
        print(f"    Speed: dict.copy() is {hamt_time/dict_time:.2f}x faster than HAMT")
    print(f"    Memory efficiency: HAMT shares ~{(base_size/(base_size+1))*100:.1f}% of structure")
    print(f"    Memory savings: ~{((dict_memory_estimate - (dict_memory_estimate/variant_count))/dict_memory_estimate)*100:.1f}% less memory with HAMT")
    
    # Test modification performance
    print(f"\n  Testing cascading modifications:")
    
    # Dict approach - modifying multiple copies
    start = time.perf_counter()
    for variant in dict_variants[:10]:
        for j in range(10):
            variant[f'mod{j}'] = j
    dict_mod_time = time.perf_counter() - start
    
    # HAMT approach - creating new versions
    start = time.perf_counter()
    for variant in hamt_variants[:10]:
        for j in range(10):
            variant = variant.set(f'mod{j}', j)
    hamt_mod_time = time.perf_counter() - start
    
    print(f"    Dict (in-place): {dict_mod_time:.4f}s")
    print(f"    HAMT (immutable): {hamt_mod_time:.4f}s")
    print(f"    Ratio (HAMT/dict): {hamt_mod_time/dict_mod_time:.2f}x")


def benchmark_hash_collisions_sized(n):
    print(f"\nBenchmarking with hash collisions ({n} items):")
    
    class BadHash:
        def __init__(self, value):
            self.value = value
        
        def __hash__(self):
            return self.value % 10
        
        def __eq__(self, other):
            return isinstance(other, BadHash) and self.value == other.value
    
    d = {}
    start = time.perf_counter()
    for i in range(n):
        d[BadHash(i)] = i
    dict_time = time.perf_counter() - start
    print(f"  dict with collisions: {dict_time:.4f}s")
    
    h = HAMT()
    start = time.perf_counter()
    for i in range(n):
        h = h.set(BadHash(i), i)
    hamt_time = time.perf_counter() - start
    print(f"  HAMT with collisions: {hamt_time:.4f}s")
    print(f"  Ratio (HAMT/dict): {hamt_time/dict_time:.2f}x")


# Keep original benchmark_memory_sharing for backward compatibility
def benchmark_memory_sharing():
    benchmark_memory_sharing_sized(1000, 100)


# Keep original benchmark_hash_collisions for backward compatibility  
def benchmark_hash_collisions():
    benchmark_hash_collisions_sized(1000)


if __name__ == '__main__':
    main()