"""
Counter and class for counting number of messages

"""
from fetching.models import Fetching
from processors.counter import ShardCounter
from fetching.meta import MessageProcessor
from google.appengine.ext import db


class MessageCounter(ShardCounter):
    """
    Represents a shard count of messages for a fetch
    """
    fetching = db.ReferenceProperty(Fetching)
    SHARDS_PER_FETCHING = 10


class CountMsg(MessageProcessor):
    """
    Keeps count of messages
    Transactionally stores in database when committed
    """
    def __init__(self, *args, **kwds):
        self.count = 0
        super(CountMsg, self).__init__(*args, **kwds)
    
    def process(self, msg, extras={}):
        self.count += 1
        
    def commit(self, extras={}):
        fetching_key = self.request_handler.fetching_key
        MessageCounter.increment(
            fetching_key=fetching_key,
            count=self.count)

