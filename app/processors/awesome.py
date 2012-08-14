"""
Grab metadata for messages with subjectively (objectively)
awesome subject lines
"""
from fetching.meta import MessageProcessor
from fetching.contacts import ContactProcessor
from processors.words import tokenize, LISTSERV_RE
from helpers.nested_dict import pset
import re
import settings

LOL_RE = re.compile(r'^l+(o+|u+)l+z*$')
SWEET_RE = re.compile(r'^swee+t$')

def awesomeness(subject):
    score = min(subject.count('!'), 6)
    for word in tokenize(subject):
        if word.startswith('congrat'):
            score += 10
        elif word == 'epic':
            score += 10
        elif word in ['awesome', 'osom']:
            if 'possum' in subject:
                score += 10
            elif 'sauce' in subject:
                score += 10
            score += 9
        elif word in ['zomg', 'omg']:
            score += 6
        elif word in ['amazing', 'cool']:
            score += 3
        elif word.startswith('hilari'):
            score += 5
        elif LOL_RE.match(word) or \
                word in ['rofl', 'roflmao','lmao', 'roflcopter']:
            score += 3
        elif word in ['hella', 'wicked']:
            score += 5
        elif word == 'great':
            score += 2
        elif word in ['fun', 'funny']:
            score += 3
        elif word in ['love', 'luv', 'bestest'] or SWEET_RE.match(word):
            score += 4
        elif word in ['fantastic', 'marvelous', 'excited',
                      'outstanding', 'sweet', 'best']:
            score += 1
        elif word in ['woot', 'w00t', '1337', 'l33t', 'wtf', 'best']:
            score += 2
    return score

class AwesomeValuationProcessor(MessageProcessor):
    def __init__(self, *args, **kwds):
        self.data = {}
        super(AwesomeValuationProcessor, self).__init__(*args, **kwds)
    
    def process(self, msg, extras={}):
        # How awesome is this message?
        if (not msg.subject) or (not isinstance(msg.subject, basestring)):
            return
        weight = awesomeness(msg.subject)
        
        if extras.get('from_user'): # User is in the "from" field
            for person in (extras['other_to'] + extras['other_cc']):
                self.handle_person(person, msg, weight)
        
        elif extras['to_user'] and extras['from_person']:
            # User is in the "to" field
            self.handle_person(extras['from_person'], msg, weight)
    
    def handle_person(self, person, msg, weight):
        if weight > 0:
            d = self.data.setdefault(person.email, {})
            d[msg.gmail_thread_id] = {
                'message_id' : msg.message_id,
                'thread_id' : msg.gmail_thread_id,               
                'awesomeness' : weight
            }
    
    def commit(self, extras={}):
        contact_data = extras.setdefault('contact_data', {})
        for email, d in self.data.iteritems():
            lst = d.values()
            lst.sort(key=(lambda d: 0-d['awesomeness']))
            pset(contact_data,
                 (email, 'awesome'),
                 lst[:settings.MAX_AWESOME])


class AwesomeCutoffProcessor(ContactProcessor):
    def imap_process(self, contact, data):
        threads = set()
        awesome_data = data.pop('awesome', [])
        awesome_data.sort(key=(lambda d: 0-d['awesomeness']))
        
        new_awesome_data = []
        for d in awesome_data:
            if len(new_awesome_data) >= settings.MAX_AWESOME:
                break
            if d['thread_id'] in threads:
                continue
            threads.add(d['thread_id'])
            new_awesome_data.append(d)
        
        data['awesome'] = []
        for d in new_awesome_data:
            message = self.get_message(d['message_id'])
            message['awesomeness'] = d['awesomeness']
            data['awesome'].append(message)
        
    def get_message(self, id_or_message):
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
