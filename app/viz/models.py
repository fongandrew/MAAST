from google.appengine.ext import db
from fetching.models import Fetching
from helpers.jsond import dumps
import hashlib


class VizData(db.Model):
    """
    Visualization data for a contact
    """
    fetching = db.ReferenceProperty(Fetching)
    contact_email = db.EmailProperty()
    contact_name = db.StringProperty()
    total_emails = db.IntegerProperty()
    
    # data for this visualization, in JSON format
    json_data = db.TextProperty()
    
    # A secret that allows this to be shared publicly
    share_key = db.StringProperty()
    
    @classmethod
    def create(cls, fetched_contact, data={}):
        """
        Create VizData object from a FetchedContact object
        """
        # Hash of key name ensures one VizData per FetchedContact
        key = cls(fetching=fetched_contact.fetching,
                  contact_email = fetched_contact.email,
                  contact_name = fetched_contact.name,
                  total_emails = fetched_contact.total_emails,
                  share_key = id_generator(),
                  json_data = dumps(data)).put()
        return key
    
    @classmethod
    def key_name_from(cls, fetched_contact_key):
        """
        Returns a key for a VizData object given a key
        for a FetchedContact object
        """
        key_base = str(fetched_contact_key)
        key_name = hashlib.sha256(key_base).hexdigest()
        return key_name


import string
import random
def id_generator(size=8):
   chars = string.ascii_uppercase + \
           string.ascii_lowercase + \
           string.digits
   return ''.join(random.choice(chars) for x in range(size))