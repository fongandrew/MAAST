"""
Code about storing aggregate data as related
to a particular contact
"""
from fetching.meta import MessageProcessor
from fetching.contacts import ContactProcessor
from fetching.models import FetchedContact
from google.appengine.ext import db
from google.appengine.api import files
import google.appengine.ext.blobstore as blobstore
import helpers.jsond as json
from helpers.nested_dict import aggregate_dicts
import logging


class JSONCounter(db.Model):
    """
    Stores a batch of counter data by keys in a JSON-encoded dict
    """
    json_data = db.TextProperty(default="{}")
    blob = blobstore.BlobReferenceProperty()
    
    def __init__(self, data={}, *args, **kwds):
        if data:
            self._data = data
        super(JSONCounter, self).__init__(*args, **kwds)
    
    def get_data(self):
        if not hasattr(self, '_data'):
            if self.blob:
                blob_reader = blobstore.BlobReader(self.blob)
                self._data = json.loads(blob_reader.read())
            else:
                self._data = json.loads(self.json_data)
        return self._data
    def set_data(self, data):
        self._data = data
    data = property(get_data, set_data)
    
    def encode(self):
        if hasattr(self, '_data'):
            self.json_data = json.dumps(self._data)
            self.blob = None
        if len(self.json_data) > 1000000: # Too big! Blobstore time.
            file_name = files.blobstore.create(mime_type='text/plain')
            with files.open(file_name, 'a') as f:
                f.write(self.json_data)
            files.finalize(file_name)
            blob_key = files.blobstore.get_blob_key(file_name)
            self.json_data = "{}"
            self.blob = blob_key
    
    @classmethod
    def aggregate(cls, parent):
        """
        Aggregate the data from all of the counters with
        a given parent
        """
        aggregate_data = {}
        for counter in cls.all().ancestor(parent):
            aggregate_dicts(aggregate_data, counter.data)
        return aggregate_data


class StoreContactCounts(MessageProcessor):
    """
    Processor that stores a JSONCounter object for a set
    of data for each contact
    """
    def process(self, *args, **kwds):
        pass
    
    def commit(self, extras={}):
        contact_data = extras.pop('contact_data', {})
        if not contact_data: return
        
        fetching_key = self.request_handler.fetching_key
        counters = []
        
        for email, data in contact_data.iteritems():
            key_name = FetchedContact.key_name_for(
                           fetching=fetching_key,
                           email=email)
            fc_key = db.Key.from_path(FetchedContact.__name__,
                                      key_name)
            
            # Assign counter name based on which FetchTask this is
            # This ensures only one JSONCounter per FetchTask and contact,
            # thereby avoiding double counting
            counter_name = str(self.request_handler.fetch_task_key)
            
            counter = JSONCounter(parent=fc_key)
            counter.data = data
            counter.encode()
            counters.append(counter)
        try:
            del data # Free up space faster
        except:
            pass # In case data doesn't exist
        
        if counters:
            try:
                db.put(counters)
            except:
                logging.warning("Splitting up large db.put")
                # Let's try splitting this up in 100 counter chunks
                for i in range(0, (len(counters) / 100) + 1):
                    smaller = counters[(i * 100):((i+1) * 100)]
                    try:
                        db.put(smaller)
                    except: # Nope, still running into an error.
                        # Do this one by one
                        for c in smaller:
                            try:
                                c.put()
                            except:
                                logging.debug(len(c.json_data))
                                logging.debug(str(c.parent))
                                logging.error("Unable to handle this")
                                pass # Ignore

class GetContactCounts(ContactProcessor):
    """
    Processor that retries and adds up data from JSONCounter object
    for a given contact
    """
    def imap_process(self, contact, data):
        """
        Not really IMAP, but do it here so IMAP processes have access to data.
        """
        agg_data = JSONCounter.aggregate(contact)
        aggregate_dicts(data, agg_data)
