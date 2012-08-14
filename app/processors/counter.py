"""
Code for aggregation, sharding, etc.
"""
from google.appengine.ext import db
import hashlib
import operator
import random

class MassCounter(db.Model):
    """
    Base class for counting LOTS of stuff. Each entity stores counts for
    multiple keys (pivots), with each key mapped to a different shard.
    
    By mapping more than one key to each counter, we lose some
    indexing abilities, but we reduce the number of transactional
    insert / puts.
    
    >>> from google.appengine.ext import testbed
    >>> tb = testbed.Testbed()
    >>> tb.activate()
    >>> tb.init_datastore_v3_stub()
    
    >>> MassCounter.increment(
    ...     {'fetching' : 'abcd'},
    ...     {'bob' : 5, 'jill' : 8})
    >>> MassCounter.increment(
    ...     {'fetching' : 'abcd'},
    ...     {'bob' : 5, 'sam' : 7})
    >>> MassCounter.increment(
    ...     {'fetching' : 'dcba'},
    ...     {'bob' : 5, 'jill' : 7})
    
    >>> print MassCounter.total({'fetching' : 'abcd'}, 'bob')
    10
    >>> print MassCounter.total({'fetching' : 'abcd'}, 'jill')
    8
    >>> print MassCounter.total({'fetching' : 'abcd'}, 'sam')
    7
    
    >>> for x,y in MassCounter.top(2, {'fetching' : 'abcd'}):
    ...     print x, y
    bob 10
    jill 8
    
    >>> tb.deactivate()
    
    """
    SHARDS = 100 # Don't change once data is stored
    
    pivot_keys = db.StringListProperty(indexed=False)
    counts = db.ListProperty(int, indexed=False)
    
    @classmethod
    def _prefix(cls, **kwds):
        """
        Creates unique name for a given set of keywords
        """
        pieces = kwds.items()
        pieces.sort()
        values = [str(value) for key, value in pieces]
        values.append(cls.__name__)
        return hashlib.sha256(' * '.join(values)).hexdigest()
    
    @classmethod
    def _shard_for(cls, pivot_key):
        """
        Returns the shard number for a given keyword (or other
        hashable object).
        """
        # Create new Random object for thread safety purposes
        r = random.Random()
        r.seed(str(pivot_key).lower().strip())
        return r.randint(1, cls.SHARDS)
    
    @classmethod
    def _validate_pivot_key(cls, pivot_key):
        """
        Override to validate and clean up pivot key
        """
        return pivot_key
    
    @classmethod
    def increment(cls, prefix_keys, pivot_counts):
        """
        Expects the following variables ...
        
        prefix_keys : dict of keys and values that all the keywords
                      have in common
        pivot_counts : dict of pivot keys to integer counts that we
                       have to increment on
        
        For example, suppose we're interested in counting the number of
        messages between User Bob and various contacts in 2009.
        
        prefix_keys might be {'user' : 'Bob', 'year' : 2009}.
        And pivot_counts would be {'Frank' : 1, 'Jill' : 7}.
        
        """
        prefix = cls._prefix(**prefix_keys)
        shard_pivot_count = {}
        
        # Sort pivot counts into appropriate shard.
        for pivot_key, value in pivot_counts.iteritems():
            pivot_key = cls._validate_pivot_key(pivot_key)
            shard_name = cls._shard_name(prefix, pivot_key)
            shard_dict = shard_pivot_count.setdefault(shard_name, {})
            shard_dict[pivot_key] = value
        
        # Increment for each shard
        for shard_name, shard_dict in shard_pivot_count.iteritems():
            db.run_in_transaction(
                cls._increment_for_shard,
                shard_name=shard_name,
                pivot_counts=shard_dict
            )
    
    @classmethod
    def _shard_name(cls, prefix, pivot_key):
        return prefix + '_' + str(cls._shard_for(pivot_key))
    
    @classmethod
    def _increment_for_shard(cls, shard_name, pivot_counts):
        """
        Gets and increments an entity with pivot counts
        
        shard_name - key_name of cls entity we're inserting 
                     pivot counts into
        
        """
        obj = cls.get_by_key_name(shard_name) or\
              cls(key_name=shard_name,
                  pivot_keys=[], counts=[])
            
        data = dict(zip(obj.pivot_keys, obj.counts))
        for pivot, count in pivot_counts.iteritems():
            data[pivot] = data.get(pivot, 0) + count
        
        obj.pivot_keys = []
        obj.counts = []
        for pivot_key, count in data.iteritems():
            obj.pivot_keys.append(pivot_key)
            obj.counts.append(count)
        
        return obj.put()
    
    @classmethod
    def total(cls, prefix_keys, pivot_key):
        """
        Gets the count for some prefix_key / pivot_key combination
        """
        pivot_key = cls._validate_pivot_key(pivot_key)
        prefix = cls._prefix(**prefix_keys) 
        shard_name = cls._shard_name(prefix, pivot_key)
        obj = cls.get_by_key_name(shard_name)
        if not obj:
            return 0
        try:
            index = obj.pivot_keys.index(pivot_key)
            return obj.counts[index]
        except (ValueError, IndexError):
            return 0
    
    @classmethod
    def get_all_for_prefix(cls, prefix_keys):
        """
        Returns all shards for given prefix keys
        """
        prefix = cls._prefix(**prefix_keys) 
        shard_names = []
        for i in range(1, cls.SHARDS + 1):
            shard_names.append(prefix + '_' + str(i))
        return filter((lambda x: x), cls.get_by_key_name(shard_names))
    
    @classmethod
    def top(cls, cutoff, prefix_keys):
        """
        Gets top X (cutoff) entries for given prefix_keys
        """
        entities = cls.get_all_for_prefix(prefix_keys)
        top_tuples = []
        for e in entities:
            if not e: continue
            tuples = zip(e.pivot_keys, e.counts)
            tuples.sort(key=(lambda x: 0 - x[1]))
            top_tuples += tuples[:cutoff]
        top_tuples.sort(key=(lambda x: 0 - x[1]))
        return top_tuples[:cutoff]
 

class MassGroupCounter(MassCounter):
    """
    Similar to MassCounter, but expects pivots to be 2-tuples.
    Shards pivots together based on first part of tuple and allows
    ranking based on the second part of the tuple.
    
    >>> from google.appengine.ext import testbed
    >>> tb = testbed.Testbed()
    >>> tb.activate()
    >>> tb.init_datastore_v3_stub()

    >>> MassGroupCounter.increment({'fetching' : 'abcd1234'},
    ...     {('a', 'bob') : 7, ('a', 'jill') : 5, ('b', 'bob') : 7})
    >>> MassGroupCounter.increment({'fetching' : 'abcd1234'},
    ...     {('a', 'jon') : 6, ('a', 'jill') : 5})
    
    >>> print MassGroupCounter.total({'fetching' : 'abcd1234'}, 'a', 'bob')
    7
    >>> print MassGroupCounter.total({'fetching' : 'abcd1234'}, 'a', 'jill')
    10
    
    >>> counts = MassGroupCounter.total({'fetching' : 'abcd1234'}, 'a')
    >>> counts.sort()
    >>> for x,y in counts:
    ...     print x,y
    bob 7
    jill 10
    jon 6
    
    >>> for x,y in MassGroupCounter.rank({'fetching' : 'abcd1234'}, 'a'):
    ...     print x,y
    jill 10
    bob 7
    jon 6

    >>> tb.deactivate()
    
    """
    pivot_groups = db.StringListProperty(indexed=False)
    
    @classmethod
    def increment(cls, prefix_keys, pivot_counts):
        """
        Expects same inputs as MassCounter except keys in pivot_counts
        should be 2-tuples of (pivot_group, pivot_key)
        """
        prefix = cls._prefix(**prefix_keys)
        shard_pivot_count = {}
        
        # Sort pivot counts into appropriate shard.
        for pivot, value in pivot_counts.iteritems():
            pivot_group, pivot_key = pivot
            pivot_group = cls._validate_pivot_group(pivot_group)
            pivot_key = cls._validate_pivot_key(pivot_key)
            shard_name = cls._shard_name(prefix, pivot_group)
            shard_dict = shard_pivot_count.setdefault(shard_name, {})
            shard_dict[(pivot_group, pivot_key)] = value
        
        # Increment for each shard
        for shard_name, shard_dict in shard_pivot_count.iteritems():
            db.run_in_transaction(
                cls._increment_for_shard,
                shard_name=shard_name,
                pivot_counts=shard_dict
            )
    
    @classmethod
    def _increment_for_shard(cls, shard_name, pivot_counts):
        """
        Expects same inputs as MassCounter except keys in pivot_counts
        should be 2-tuples of (pivot_group, pivot_key)
        """
        obj = cls.get_by_key_name(shard_name) or\
              cls(key_name=shard_name,
                  pivot_keys=[], pivot_groups=[], counts=[])
            
        data = dict(zip(zip(obj.pivot_groups, obj.pivot_keys),
                        obj.counts))
        for pivot, count in pivot_counts.iteritems():
            data[pivot] = data.get(pivot, 0) + count
        
        obj.pivot_keys = []
        obj.pivot_groups = []
        obj.counts = []
        for pivot, count in data.iteritems():
            pivot_group, pivot_key = pivot
            obj.pivot_groups.append(pivot_group)
            obj.pivot_keys.append(pivot_key)
            obj.counts.append(count)
        
        return obj.put()
    
    @classmethod
    def _validate_pivot_group(cls, pivot_group):
        """
        Override to validate and clean up pivotgroup
        """
        return pivot_group
    
    @classmethod
    def total(cls, prefix_keys, pivot_group, pivot_key=None):
        """
        Gets the count for some prefix_key / pivot_key combination
        """
        if not pivot_key:
            return cls._get_counts_for_group(prefix_keys, pivot_group)
        
        prefix = cls._prefix(**prefix_keys) 
        pivot_group = cls._validate_pivot_group(pivot_group)
        pivot_key = cls._validate_pivot_key(pivot_key)
        shard_name = cls._shard_name(prefix, pivot_group)
        obj = cls.get_by_key_name(shard_name)
        if not obj:
            return 0
        try:
            pivots = zip(obj.pivot_groups, obj.pivot_keys)
            index = pivots.index((pivot_group, pivot_key))
            return obj.counts[index]
        except (ValueError, IndexError):
            return 0
    
    @classmethod
    def _get_counts_for_group(cls, prefix_keys, pivot_group):
        pivot_group = cls._validate_pivot_group(pivot_group)
        prefix = cls._prefix(**prefix_keys) 
        shard_name = cls._shard_name(prefix, pivot_group)
        obj = cls.get_by_key_name(shard_name)
        
        results = []
        if obj:
            for g,k,c in zip(obj.pivot_groups,
                             obj.pivot_keys,
                             obj.counts):
                if g == pivot_group:
                    results.append((k, c))
        
        return results
    
    @classmethod
    def rank(cls, prefix_keys, pivot_group):
        """
        Top X counts with given prefix_keys and pivot_group
        """
        results = cls._get_counts_for_group(prefix_keys, pivot_group)
        results.sort(key=(lambda t: 0 - t[1]))
        return results
    
    top = rank


class ShardCounter(db.Model):
    """
    Base class for counting something
    """
    count = db.IntegerProperty(default=0)
    
    SHARDS_PER_FETCHING = 10
    
    @classmethod
    def prefix(cls, **kwds):
        """
        Creates unique name for a given set of keywords
        """
        pieces = kwds.items()
        pieces.sort()
        values = [str(value) for key, value in pieces]
        return hashlib.sha256(' * '.join(values)).hexdigest()
    
    @classmethod
    def increment(cls, **kwds):
        incr_by = kwds.pop('count', 1)
        prefix = cls.prefix(**kwds)
        
        def do_incr():
            shard = random.randint(1, cls.SHARDS_PER_FETCHING)
            key_name = prefix + '_' + str(shard)
            mc = cls.get_by_key_name(key_name)
            if mc is None:
                mc = cls(key_name=key_name, count=0, **kwds)
                # for key, value in kwds.items():
                #     setattr(mc, key, value)
            mc.count += incr_by
            mc.put()
        
        db.run_in_transaction(do_incr)
    
    @classmethod
    def total(cls, **kwds):
        prefix = cls.prefix(**kwds)
        
        key_names = []
        for shard in range(1, cls.SHARDS_PER_FETCHING + 1):
            key_names.append(prefix + '_' + str(shard))
        
        return sum([counter.count if counter else 0
                    for counter in cls.get_by_key_name(key_names)])
    
    @classmethod
    def top(cls, cutoff=10, offset=0, **kwds):
        """
        Kwds should include all properties except count and one
        other property. Return tuple of top X options for remaining
        property and counts.
        
        """
        props = cls.properties().keys()
        props.remove('count')
        for key in kwds:
            props.remove(key)
        pivot = props[0]
        
        if cls.SHARDS_PER_FETCHING == 1:
            q = cls.all()
            for key, value in kwds.items():
                q = q.filter(key + ' =', value)
            q.order('-count')
            return [(getattr(obj, pivot), obj.count)
                         for obj in q.fetch(cutoff, offset=offset)]
        
        # Haven't figured this out for shards > 1
        # Probably just loop, but could be very slow.
        raise NotImplementedError("To do.")

    
    
    


