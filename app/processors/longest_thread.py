from fetching.meta import MessageProcessor
from fetching.contacts import ContactProcessor
from helpers.nested_dict import pincr, aggregate_dicts
from processors.counter import MassCounter
import datetime
import logging

class ThreadCounter(MassCounter):
    """
    Represents a shard count for each thread id
    """
    # id_keys - fetching keys
    # pivot_keys - list of gmail thread ids
    SHARDS = 10 # Don't change once data is stored

class UserThreadCounter(MassCounter):
    """
    Represents a shard count of user's messages to each thread
    """
    # id_keys - fetching keys
    # pivot_keys - list of gmail thread ids
    SHARDS = 10 # Don't change once data is stored
    

class TrackThreadContactProcessor(MessageProcessor):
    """
    Tracks which contacts have communicated to which threads
    and which thread is longest
    """
    def __init__(self, *args, **kwds):
        self.thread_contacts = {}
        self.thread_counts = {}
        self.user_threads = {}
        super(TrackThreadContactProcessor, self).__init__(*args, **kwds)
    
    def process(self, msg, extras={}):
        # Get message count for thread
        thread_id = msg.gmail_thread_id
        self.thread_counts[thread_id] = \
            self.thread_counts.get(thread_id, 0) + 1
        
        # We're only interested in thread if user sends a message to it
        if extras.get('from_user'):
            self.user_threads[thread_id] = \
                self.user_threads.get(thread_id, 0) + 1
        
        # To be associated with a thread, contact must send message
        # as "from" contact. So record sender if not from user.
        else:
            from_person = extras.get('from_person')
            if from_person:
                email = from_person.email
                self.thread_contacts.setdefault(email, set())\
                                    .add(thread_id)
    
    def commit(self, extras={}):
        # JSONCounter data
        contact_data = extras.setdefault('contact_data', {})
        for contact, thread_set in self.thread_contacts.iteritems():
            contact_data[contact]['threads'] = thread_set
        
        # Commit actual counts
        fetching_key = self.request_handler.fetching_key
        prefix_keys = {'fetching' : fetching_key}
        UserThreadCounter.increment(prefix_keys, self.user_threads)
        ThreadCounter.increment(prefix_keys, self.thread_counts)


class SortThreadsProcessor(ContactProcessor):
    """
    Gets thread counts and picks out the longest one
    """
    def __init__(self, *args, **kwds):
        super(SortThreadsProcessor, self).__init__(*args, **kwds)
        fetching_key = self.request_handler.fetching_key
        prefix_keys = {'fetching' : fetching_key}
        
        counters = ThreadCounter.get_all_for_prefix(prefix_keys) 
        counts = []
        for tc in counters:
            counts += zip(tc.pivot_keys, tc.counts)
        self.thread_counts = dict(counts)
        del counts
        
        counters = UserThreadCounter.get_all_for_prefix(prefix_keys) 
        counts = []
        for utc in counters:
            counts += zip(utc.pivot_keys, utc.counts)
        self.user_threads = dict(counts)
        del counts
    
    def post_process(self, contact, data):
        threads = set(data.pop('threads', []))
        data['num_threads'] = len(threads)
        
        thread_list = []
        for thread_id in threads:
            if thread_id in self.user_threads:
                thread_list.append(
                    (self.thread_counts[thread_id], thread_id))
        if not thread_list:
            for thread_id in threads:
                thread_list.append(
                    (self.thread_counts[thread_id], thread_id))
        thread_list.sort()
        longest_count, longest_id = thread_list[-1]
        
        # Get first message in longest thread
        thread_data = self.account.get_thread(longest_id)
        start_date = datetime.datetime(2100,1,1)
        end_date = datetime.datetime(1960,1,1)
        subject = ''
        for msg in thread_data['messages']:
            msg_date = datetime.datetime.fromtimestamp(msg['date'])
            start_date = min(msg_date, start_date)
            end_date = max(msg_date, end_date)
            if (not subject) or len(subject) >= msg['subject']:
                subject = msg['subject']
        while subject.startswith('Re: ') or subject.startswith('Fw: '):
            subject = subject[4:]
        
        # Set data
        data['longest_thread'] = {
            'gmail_thread_id' : longest_id,
            'num_messages' : longest_count,
            'subject' : subject,
            'start_date' : start_date,
            'end_date' : end_date
        }
