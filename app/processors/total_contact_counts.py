"""
Counter and class for identifying "top" contacts

"""
from fetching.models import Fetching
from processors.counter import MassCounter
from fetching.meta import MessageProcessor
from google.appengine.ext import db
import datetime
import logging, time

class ContactCounter(MassCounter):
    """
    Represents a shard count of messages from contact to user or vice versa
    """
    # id_keys - fetching keys
    
    # pivot_keys - list of contact emails
    @classmethod
    def _validate_pivot_key(cls, pivot_key):
        assert '@' in pivot_key, "Pivot key must be contact email address"
        return pivot_key
        
    SHARDS = 10 # Don't change once data is stored

class ToContactCounter(MassCounter):
    """
    Represents a shard count of messages from user to contact
    """
    # id_keys - fetching keys
    
    # pivot_keys - list of contact emails
    @classmethod
    def _validate_pivot_key(cls, pivot_key):
        assert '@' in pivot_key, "Pivot key must be contact email address"
        return pivot_key
        
    SHARDS = 10 # Don't change once data is stored

class FromContactCounter(MassCounter):
    """
    Represents a shard count of messages from contact to user
    """
    # id_keys - fetching keys
    
    # pivot_keys - list of contact emails
    @classmethod
    def _validate_pivot_key(cls, pivot_key):
        assert '@' in pivot_key, "Pivot key must be contact email address"
        return pivot_key
        
    SHARDS = 10 # Don't change once data is stored


class CountContactProcessor(MessageProcessor):
    def __init__(self, *args, **kwds):
        self.total_counts = {}
        self.to_counts = {}
        self.from_counts = {}
        super(CountContactProcessor, self).__init__(*args, **kwds)
    
    def process(self, msg, extras={}):
        if extras.get('from_user'):
            for person in extras['all_others']:
                self.incr(person, 'total_counts')
                self.incr(person, 'to_counts')
        
        elif extras['from_person']:
            from_person = extras['from_person']
            self.incr(from_person, 'total_counts')
            self.incr(from_person, 'from_counts')
        
    def incr(self, person, dict_name='total_counts'):
        d = getattr(self, dict_name)
        if person and person.email:
            d[person.email] = d.get(person.email, 0) + 1
    
    def commit(self, extras={}):
        fetching_key = self.request_handler.fetching_key
        prefix_keys = {'fetching' : fetching_key}
        ContactCounter.increment(prefix_keys, self.total_counts)
        ToContactCounter.increment(prefix_keys, self.to_counts)
        FromContactCounter.increment(prefix_keys, self.from_counts)
    

    