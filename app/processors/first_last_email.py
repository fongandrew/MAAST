from fetching.meta import MessageProcessor
from fetching.contacts import ContactProcessor
from helpers.nested_dict import aggregate_dicts, pget
import datetime, math
import logging

class TrackFirstLastEmail(MessageProcessor):
    """
    Keeps track of the first and last e-mail per contact in each batch
    Only includes people in "from" and "to" fields, not CC
    """
    def __init__(self, *args, **kwds):
        self.data = {}
        super(TrackFirstLastEmail, self).__init__(*args, **kwds)
    
    def process(self, msg, extras={}):
        from_person = msg.addresses['from']
        to_persons = msg.addresses['to']
        
        if extras.get('from_user'): # User is in the "from" field
            for person in extras['other_to']:
                self.handle_person(person, msg)
        
        elif extras.get('to_user'): # User is in the "to" field
            self.handle_person(from_person, msg)
    
    def handle_person(self, person, msg):
        if person and person.email:
            data = self.data.setdefault(person.email, {
                'first_email' : [(datetime.datetime(2100,1,1), None)],
                'last_email' : [(datetime.datetime(1960,1,1), None)]
            })
            if data['first_email'][0][0] > msg.date:
                data['first_email'] = [(msg.date, msg.message_id)]
            if data['last_email'][0][0] < msg.date:
                data['last_email']  = [(msg.date, msg.message_id)]
    
    def commit(self, extras={}):
        extras.setdefault('contact_data', {})
        aggregate_dicts(extras['contact_data'], self.data)


class GetFirstLastEmail(ContactProcessor):
    """
    Using message ids from message processing, get first / last email
    bodies via IMAP.
    """
    def imap_process(self, contact, data):
        first_email_list = data.get('first_email', [])
        if first_email_list:
            first_email_id = min(first_email_list)[1]
            data['first_email'] = self.get_message(first_email_id)
        
        last_email_list = data.get('last_email', [])
        if last_email_list:
            last_email_id = max(last_email_list)[1]
            if last_email_id != first_email_id:
                data['last_email'] = self.get_message(last_email_id)
        
        # Middle e-mail
        # Get total mail count and find a rounded "middle" count, e.g.
        #   1024 => 500
        #   2100 => 1000
        #   500 => 200
        #   1900 => 900
        total = (pget(data, ('from', 'total')) or 0) +\
                (pget(data, ('to', 'total')) or 0)
        total = int(total)
        if total > 2:
            base = 10 ** int(math.log(total/2, 10))
            # This may look like base should cancel out, but we're taking
            # advantage of the round-down aspect of int-typing.
            mid_int = (total / (2 * base)) * base
            offset = total - mid_int
            
            message = self.account.get_messages_for_contact(contact.email,
                                       offset=offset, limit=1)
            if message:
                data['middle_email'] = self.get_message(message[0])
                data['middle_email']['number'] = mid_int
        else:
            logging.warning("No middle e-mail! Less than 3 e-mails!")
        
    
    def get_message(self, id_or_message):
        if hasattr(id_or_message, 'subject'):
            message = id_or_message
        else:
            message = self.account.get_message(id_or_message)
        return {
            'from' : {
                'email' : message.addresses['from'].email,
                'name' : message.addresses['from'].name
            } if message.addresses.get('from', None)
              else {},
            
            'to' : [{
                'email' : person.email,
                'name' : person.name
            } for person in message.addresses['to']
              if (person and person.email)],
            
            'cc' : [{
                'email' : person.email,
                'name' : person.name
            } for person in message.addresses['cc']
              if (person and person.email)],
            
            'gmail_message_id' : message.gmail_message_id,
            'subject' : message.subject,
            'date' : message.date,
            'body' : message.get_body()[:500]
        }
        
        
    
    
    