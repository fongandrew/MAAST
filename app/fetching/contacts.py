from fetching.base import ContextIOWorker
from fetching.models import FetchedContact
from viz.models import VizData
from helpers.real_people import real_person, equivalent
from google.appengine.ext import db
import logging


class FetchForContactWorker(ContextIOWorker):
    """
    Creates contact objects based on fetched entities
    """
    UNIQUE_PARAM_SET = ['offset']
    
    @classmethod
    def add_task(cls, *args, **kwds):
        # Potential for workers to run in parallel, and if they fail
        # they may try to recreate each other, so must be unique
        kwds['unique'] = True
        kwds['queue_name'] = 'contacts'
        kwds['target'] = 'contacts'
        super(FetchForContactWorker, cls).add_task(*args, **kwds)
    
    def post(self):
        """
        Needs following variables
        
        fetching_key - key of Fetching object we're processing
                       contacts for (required)
        offset - 0-based integer for which contact in fetching
                 we're analyzing
        
        """
        offset = int(self.request.get('offset') or 0)
        try:
            contact_key = self.fetching.init_fetched_contacts[offset]
        except IndexError:
            logging.error(
                "Fetching %s does not have contact key offset %s"
                 % (self.fetching_key, offset))
            return
        
        self.contact = FetchedContact.get(contact_key)
        if not self.contact:
            logging.error(
                "Contact not found for key %s, fetching %s, offset %s"
                 % (contact_key, self.fetching_key, offset))
            return
        
        # This will be used to create viz later
        self.data = {}
        
        # Instantiate processor classes
        self.init_processors()
        
        # Modify self.data with sequential stuff
        self.do_imap_process()
        
        # Create new worker than can run in parallel
        offset += 1
        if len(self.fetching.init_fetched_contacts) > offset:
            self.replicate(params={'offset' : offset})
        
        # Finish up parpllel tasks
        self.do_post_process()
        
        # Create visualization
        viz_data_key = VizData.create(self.contact, self.data)
        
        # Save to contact
        self.contact.viz_data_id = str(viz_data_key.id_or_name())
        self.contact.put()
    
    def init_processors(self):
        # This is where processors are listed
        # Make sure they're loaded
        import processors.register
        # Actual instantiation
        self.processors = [cls(self) for cls in self.processor_clses]
    
    def do_imap_process(self):
        for processor in self.processors:
            processor.imap_process(self.contact, self.data)
    
    def do_post_process(self):
        for processor in self.processors:
            processor.post_process(self.contact, self.data)
    
    @classmethod
    def register_processor(cls, func):
        """
        Call to register a processor that will process a message. Each processor
        should be a subclass of MessageProcessor (below).
        
        """
        if not func in cls.processor_clses:
            cls.processor_clses.append(func)
            return True
    processor_clses = []


class ContactProcessor(object):
    """
    Base class for a callable that processes a contact
    """
    def __init__(self, request_handler):
        """
        Initialize with reference to request handler
        """
        self.request_handler = request_handler
        self.account = request_handler.account
    
    def imap_process(self, contact, data):
        """
        Processing of a contact that depend on IMAP access via
        Context.IO and therefore should not be run in parallel
        with processing of other contacts
        
        contact - FetchedContact object representing this contact
                  Has name, email, and fetching variables set.
        
        data - Dict that will be passed to visualization.
               Modify as appropriate.
        
        """
        pass
    
    def post_process(self, contact, data):
        """
        Processing of a contact that does not depend on IMAP
        access and therefore should can be run in parallel
        with processing of other contacts
        
        contact - FetchedContact object representing this contact
                  Has name, email, and fetching variables set.
        
        data - Dict that will be passed to visualization.
               Modify as appropriate.
        
        """
        pass


def register_processor(func):
    FetchForContactWorker.register_processor(func)