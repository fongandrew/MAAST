def pget(dct, keys=[]):
    """
    Get nested path for dict
    """
    for key in keys:
        if key in dct:
            dct = dct[key]
        else:
            return None
    return dct
 
def pset(dct, keys, value):
    """
    Sets nested path for dict
    
    >>> dct = {}
    >>> pset(dct, ("a", "b", "c"), 5)
    >>> pset(dct, ("a", "b", "d"), 6)
    >>> pget(dct, ("a", "b", "c"))
    5
    >>> pget(dct, ("a", "b", "d"))
    6
    >>> pget(dct, ("a", "b", "e"))
    >>> dct
    {'a': {'b': {'c': 5, 'd': 6}}}
    
    """
    assert len(keys)
    last_key = keys[-1]
    keys = keys[:-1]
    for key in keys:
        if key in dct:
            dct = dct[key]
        else:
            dct[key] = {}
            dct = dct[key]
    dct[last_key] = value

def pincr(dct, keys, count=1, default=0):
    """
    >>> dct = {}
    >>> pincr(dct, ('a', 'b', 'c'), 5)
    >>> pincr(dct, ('a', 'b', 'c'), 5)
    >>> pincr(dct, ('a', 'b', 'd'), 5)
    >>> pget(dct, ('a', 'b', 'c'))
    10
    >>> pget(dct, ('a', 'b', 'd'))
    5
    
    """
    current = pget(dct, keys) or default
    pset(dct, keys, current + count)


def aggregate_dicts(d1, d2):
    """
    Sum up counts from dicts -- modifying the first dict
    
    >>> d1 = {'a' : 1, 'b' : 2,
    ...       'c' : {'a' : 3,
    ...              'b' : 4,
    ...              'c' : [1,2,3]}}
    >>> d2 = {'a' : 2, 'b' : 3,
    ...       'c' : {'a' : 4,
    ...              'b' : 5,
    ...              'c' : [4,5,6]}}
    >>> aggregate_dicts(d1, d2)
    >>> d1['a']
    3
    >>> d1['b']
    5
    >>> d1['c']['a']
    7
    >>> d1['c']['b']
    9
    >>> d1['c']['c']
    [1, 2, 3, 4, 5, 6]
    
    """
    for key, value in d2.iteritems():
        if not key in d1:
            d1[key] = value
        elif hasattr(value, 'iteritems'):
            aggregate_dicts(d1[key], value)
        else:
            d1[key] += value
