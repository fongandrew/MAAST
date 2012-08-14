"""
Models used in fetching e-mails
"""
from google.appengine.ext import db
from helpers.clean import clean_str
import hashlib
import logging
import settings


class Fetching(db.Model):
    """
    Represents a single attempt to fetch a user's inbox
    """
    # Google User Account
    user = db.UserProperty(auto_current_user_add=True,
                           required=True)
    # E-mail address of account as stored on Context.IO
    email = db.EmailProperty(required=True)
    
    # Timing of when fetch was created
    fetched_on = db.DateTimeProperty(auto_now_add=True)
    
    # Seconds since epoch of last sync, as stored on Context.IO
    timing = db.IntegerProperty()
    
    # Have we finished getting initial meta data and processing it?
    meta_complete = db.BooleanProperty(default=False)
    
    # Have we finished creating initial visualizations for contacts?
    viz_complete = db.BooleanProperty(default=False)
    
    # List of initial contacts by FetchedContact key
    init_fetched_contacts = db.ListProperty(db.Key)
    
    # Other stats
    num_emails = db.IntegerProperty(default=0)
    num_to_emails = db.IntegerProperty(default=0)
    num_from_emails = db.IntegerProperty(default=0)
    avg_emails = db.FloatProperty(default=0.0)
    avg_to_emails = db.FloatProperty(default=0.0)
    avg_from_emails = db.FloatProperty(default=0.0)
    
    @classmethod
    def create(cls, email):
        email = str(email).lower().strip()
        parent = FetchingParent(key_name=email).put()
        return cls(parent=parent, email=email).put()
    
    @classmethod
    def get_most_recent(cls, email):
        email = str(email).lower().strip()
        parent_key = db.Key.from_path(FetchingParent.__name__, email)
        fetching = cls.all()\
                      .ancestor(parent_key)\
                      .order('-fetched_on')\
                      .fetch(1)
        if fetching:
            return fetching[0]
        else:
            logging.warning("Unable to find most recent Fetching for %s" % email)

class FetchingParent(db.Model):
    """
    An entity to be used as a parent for Fetching object creation
    to ensure that user does not accidentally create multiple
    Fetching objects in quick sequence.
    """


class FetchTask(db.Expando):
    """
    Used to track uncompleted tasks, or maintain task uniqueness.
    Used by ContextIOWorker.
    """
    complete = db.BooleanProperty(default=False)
    fetch_task_tries = db.IntegerProperty(default=0)


class FetchedContact(db.Model):
    """
    Represents a contact from a particular fetching
    """
    fetching = db.ReferenceProperty(Fetching, required=True)
    email = db.EmailProperty(required=True)
    name = db.StringProperty()
    total_emails = db.IntegerProperty(default=0)
    viz_data_id = db.StringProperty()
    
    @classmethod
    def key_name_for(cls, fetching, email, **kwds):
        """
        Returns key_name given correct fetching and email
        """
        if hasattr(fetching, 'key') and callable(fetching.key):
            fetching = fetching.key()
        pre_name = str(fetching) + '_' + str(email)
        return hashlib.sha256(pre_name).hexdigest()
    
    @classmethod
    def create(cls, put=True, **kwds):
        """
        Creates FetchedContact with proper key
        """
        key_name = cls.key_name_for(**kwds)
        kwds['name'] = clean_str(kwds.get('name', ''))
        obj = cls(key_name=key_name, **kwds)
        if put:
            return obj.put()
        else:
            return obj

    @classmethod
    def get_by_params(cls, *args, **kwds):
        """
        Gets correct FetchedContact given fetching key
        and contact e-mail
        """
        key_name = cls.key_name_for(*args, **kwds)
        return cls.get_by_key_name(key_name)
    
