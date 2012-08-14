"""
Processor that identifies and creates a new FetchedContact
using the from / to / cc data
"""
from fetching.models import Fetching, FetchedContact
from fetching.meta import MessageProcessor
from google.appengine.ext import db
import logging, time

class CreateContact(MessageProcessor):
    def __init__(self, *args, **kwds):
        self.contacts = {}
        super(CreateContact, self).__init__(*args, **kwds)
    
    def process(self, msg, extras={}):
        from_person = msg.addresses['from']
        to_persons = msg.addresses['to']
        cc_persons = msg.addresses['cc']
        
        # Create entries for each actual person
        for person in (to_persons + cc_persons):
            self.add_contact(person)
        self.add_contact(from_person)
    
    def add_contact(self, contact):
        if contact and contact.email:
            self.contacts[contact.email] = contact
    
    def create_contact_model(self, contact):
        return FetchedContact.create(
            put = False,
            fetching = self.fetching_key,
            email = contact.email,
            name = contact.name,
            total_emails = 0 # Update later once finish counting
        )
    
    def commit(self, extras={}):
        self.fetching_key = self.request_handler.fetching_key
        contacts = [self.create_contact_model(contact)
                    for contact in self.contacts.values()]
        
        # start = time.time()
        db.put(contacts)
        # end = time.time()
        # logging.debug("Commited %s contacts in %s seconds" %
        #                (len(contacts), (end - start)))
    

