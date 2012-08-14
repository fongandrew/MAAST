"""
Counter and class for counting which contacts go where

"""
from fetching.models import Fetching
from fetching.meta import MessageProcessor
from fetching.contacts import ContactProcessor
from google.appengine.ext import db
from helpers.nested_dict import pincr, aggregate_dicts
import datetime
import settings
import logging, time

class CountContactMsg(MessageProcessor):
    """
    Keeps count of messages
    Transactionally stores in database when committed
    """
    def __init__(self, *args, **kwds):
        self.data = {}
        super(CountContactMsg, self).__init__(*args, **kwds)        
    
    def process(self, msg, extras={}):
        # Get month to pass along as well
        msg_month = datetime.date(
                        year = msg.date.year,
                        month = msg.date.month,
                        day = 1)
        msg_hour = msg.date.hour
        
        # Record who we're sending to
        if extras.get('from_user'):
            for person in extras['all_others']:
                if person and person.email:
                    pincr(self.data,
                            (person.email, 'to', 'total'))
                    pincr(self.data,
                            (person.email, 'to', 'month', str(msg_month)))
                    pincr(self.data,
                            (person.email, 'to', 'hour', str(msg_hour)))
            
        elif extras.get('from_person'): # To user
            from_person = extras.get('from_person')
            pincr(self.data,
                    (from_person.email, 'from', 'total'))
            pincr(self.data,
                    (from_person.email, 'from', 'month', str(msg_month)))
            pincr(self.data,
                    (from_person.email, 'from', 'hour', str(msg_hour)))
        
        
        # Get contact-to-contact pairs / CCed conctacts
        for person in extras['all_others']:
            for other_person in extras['all_others']:
                email = person.email
                other_email = other_person.email
                if email == other_email: continue
                pincr(self.data,
                        (email, 'cc', other_email, 'total'))
                pincr(self.data,
                        (email, 'cc', other_email,
                         'year', str(msg_month.year)))
    
    def commit(self, extras={}):
        extras.setdefault('contact_data', {})
        aggregate_dicts(extras['contact_data'], self.data)

class ProcessContactMsg(ContactProcessor):
    def post_process(self, contact, data):
        """
        Cut off really long cc lists
        """
        cc_data = data.get('cc', None)
        if not cc_data: return
        
        total_cc = []
        yearly_cc = {}
        
        for cc_email, cc_dict in cc_data.iteritems():
            total_cc.append((cc_email, cc_dict['total']))
            for year, count in cc_dict['year'].iteritems():
                yearly_cc.setdefault(str(year), [])\
                         .append((cc_email, count))
        
        sorting_hat = (lambda x: 0 - x[1])
        total_cc.sort(key=sorting_hat)
        del total_cc[settings.TOP_CC_COUNT:]
        
        for counts in yearly_cc.values():
            counts.sort(key=sorting_hat)
            del counts[settings.TOP_CC_COUNT:]
        
        data['cc'] = {
            'total' : total_cc,
            'yearly' : yearly_cc
        }

    
    