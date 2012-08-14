"""
Code for starting and completing other tasks
"""
from fetching.base import ContextIOWorker, ContextIORequest
from fetching.models import Fetching, FetchTask, FetchedContact
from fetching.meta import FetchCountWorker, FetchMetaWorker
from fetching.contacts import FetchForContactWorker 
from google.appengine.ext import db
from helpers.routing import url_for
from helpers.real_people import equivalent, real_person
import logging, time
import settings


class FirstLoginHandler(ContextIORequest):
    """
    The first handler called for a user logging in
    Creates other worker tasks
    """
    def get(self):
        """
        Placeholder, asks user if they want to do this.
        """
        return self.post()
    
    def post(self):
        """
        Adds Fetching tasks task 
        """
        fetching_key = Fetching.create(email=self.email)
        
        # Add worker to get count
        FetchCountWorker.add_task(fetching_key)
        
        # Add worker to incrementally get emails
        FetchMetaWorker.add_task(fetching_key)
        
        # Add worker to check for when other tasks are done
        FetchCompletionWorker.add_task(fetching_key)
        
        # Redirect to loading / status page
        from fetching.status import StatusPage
        self.redirect(url_for(StatusPage))


class FetchCompletionWorker(ContextIOWorker):
    """
    Worker that checks for whether our FetchMetaWorker tasks have
    completed. Retries if not.
    """    
    @classmethod
    def add_task(cls, fetching_key, params={}, **kwds):
        # Doesn't have to be unique (only called once by function)
        kwds['unique'] = False
        kwds['queue_name'] = 'init'
        kwds['countdown'] = 60
        return super(FetchCompletionWorker, cls).add_task(
            fetching_key=fetching_key, params=params, **kwds)
    
    def post(self):
        """
        Accepts the following arguments
        
        fetching_key - Fetching key (required)
        
        """         
        # If there are still ongoing tasks
        if self.active():
            if not self.replicate():
                logging.warning("Unable to replicate for fetching %s"
                    % str(self.fetching_key))
            return # quit
        
        if self.fetching.meta_complete:
            logging.debug("Completing fetching %s"
                % str(self.fetching_key))
            # Meta is already complete, so expiration of tasks
            # must mean we've finished viz
            self.fetching.viz_complete = True
            # Save fetching, we're done
            self.fetching.put()
        else:
            # Note meta completion
            self.fetching.meta_complete=True
            # Create contacts
            self.fetching.init_fetched_contacts = self.get_contacts()
            # Save fetching, so contact worker has something to look at
            self.fetching.put()
            # Create a task worker to process contacts
            FetchForContactWorker.add_task(self.fetching_key)
            # Replicate to check later
            if not self.replicate():
                logging.warning("Unable to replicate for fetching %s"
                    % str(self.fetching_key))
    
    def get_contacts(self, count=settings.NUM_CONTACTS):
        """
        Create top contacts (up to count), returns number created
        """
        from processors.total_contact_counts import ToContactCounter,\
                                                    FromContactCounter,\
                                                    ContactCounter
        limit = count * 2
        offset = 0
        name = self.account.first_name + " " + self.account.last_name
        name = name.strip()
        email = self.email
        top_contacts = []
        
        prefix = {'fetching' : self.fetching_key}
        
        # Add up totals and get averages
        total = []
        for counter in ContactCounter.get_all_for_prefix(prefix):
            total += counter.counts
        num_emails = sum(total)
        num_contacts = len(total)
        fetching = self.fetching
        fetching.num_emails = num_emails
        fetching.avg_emails = num_emails / float(num_contacts)
        
        total_to = []
        for counter in ToContactCounter.get_all_for_prefix(prefix):
            total_to += counter.counts
        num_emails = sum(total_to)
        num_contacts = len(total_to)
        fetching.num_to_emails = num_emails
        fetching.avg_to_emails = num_emails / float(num_contacts)
        
        total_from = []
        for counter in FromContactCounter.get_all_for_prefix(prefix):
            total_from += counter.counts
        num_emails = sum(total_from)
        num_contacts = len(total_from)
        fetching.num_from_emails = num_emails
        fetching.avg_from_emails = num_emails / float(num_contacts)
        
        def get_top_contacts(offset):
            e_c = ToContactCounter.top(limit * (1 + offset),
                    {'fetching' : self.fetching_key})[offset:]
            key_names = [
                FetchedContact.key_name_for(self.fetching_key, email)
            for email, count in e_c]
            fetched_contacts = FetchedContact.get_by_key_name(key_names)
            
            for tup, f_c in zip(e_c, fetched_contacts):
                count = tup[1]
                f_c.total_emails = count
            
            return fetched_contacts
        
        while len(top_contacts) < count:
            for contact in get_top_contacts(offset):
                if len(top_contacts) >= count:
                    break
                if not contact.email:
                    continue
                if equivalent(name, email, contact):
                    continue
                if not real_person(contact):
                    continue
                if not FromContactCounter.total(prefix, contact.email):
                    continue
                top_contacts.append(contact)
            offset += limit
        
        return db.put(top_contacts)
    
    def active(self):
        """
        Returns whether FetchTasks for a given fetching key (in str form)
        is still running.
        
        """
        q = FetchTask.all()\
                     .ancestor(self.fetching_key)\
                     .filter('complete =', False)
        results = q.fetch(100)
        if results:
            completed_tasks = []
            for task in results:
                if task.fetch_task_tries >= settings.MAX_RETRIES:
                    task.complete = True
                    completed_tasks.append(task)
            db.put(completed_tasks)    
            return True
        return False

