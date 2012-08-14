"""
Model and handler for tracking latest e-mails for a fetching
"""
from fetching.models import Fetching
from helpers.clean import clean_str
from google.appengine.ext import db
import random
import logging, time

class FetchedMessage(db.Model):
    """
    Represents a single fetched message
    """
    fetching = db.ReferenceProperty(Fetching)
    
    gmail_message_id = db.StringProperty()
    from_email = db.EmailProperty(indexed=False)
    from_name = db.StringProperty(indexed=False)
    to_emails = db.ListProperty(db.Email, indexed=False)
    to_names = db.StringListProperty(indexed=False)
    subject = db.StringProperty(indexed=False)
    date = db.DateTimeProperty()
    
    @classmethod
    def from_context(cls, msg):
        """
        Creates object from Context.IO type, does not put
        
        """
        params = {}
        from_person = msg.addresses['from']
        if from_person:
            if from_person.email:
                params['from_email'] = db.Email(from_person.email)
            if from_person.name:
                params['from_name'] = clean_str(from_person.name)
        
        to_persons = msg.addresses['to'] or []
        params['to_emails'] = []
        params['to_names'] = []
        for person in to_persons:
            if person.email:
                params['to_emails'].append(db.Email(person.email))
                if person.name:
                    params['to_names'].append(clean_str(person.name))
                else:
                    params['to_names'].append("")
        
        params['subject'] = clean_str(msg.subject)
        params['date'] = msg.date
        params['gmail_message_id'] = msg.gmail_message_id
        
        return cls(**params)


# Processor base class
from fetching.meta import MessageProcessor

class SaveFetchedMsg(MessageProcessor):
    def __init__(self, *args, **kwds):
        self.messages = []
        super(SaveFetchedMsg, self).__init__(*args, **kwds)
    
    def process(self, msg, extras={}):
        """
        Randomly creates messages addressed to user
        
        """
        if not extras.get('from_user') and \
                random.randint(0,32) == 27:
            msg = FetchedMessage.from_context(msg)
            msg.fetching = self.request_handler.fetching_key
            self.messages.append(msg)
    
    def commit(self, extras={}):
        """
        Saves messages to datastore
        """
        db.put(self.messages)

