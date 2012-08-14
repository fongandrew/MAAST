"""
Code in user synonym
"""
from helpers.real_people import equivalent
from fetching.meta import MessageProcessor

class UserID(MessageProcessor):
    def process(self, msg, extras):
        """
        If the message is from the user who's inbox we're trawling,
        set the extras dict appropriately
        """
        from_person = msg.addresses['from']
        to_persons = msg.addresses['to']
        cc_persons = msg.addresses['cc']
        
        # Spammy message, ignore!
        if (len(to_persons) + len(cc_persons)) > 60:
            extras['STOP_PROCESSING'] = True
            return
        
        # No date? Quit!
        if not msg.date:
            extras['STOP_PROCESSING'] = True
            return
        
        if not (from_person and from_person.email):
            extras['STOP_PROCESSING'] = True
            return
        
        rh = self.request_handler
        
        account = rh.account
        name = account.first_name + " " + account.last_name
        name = name.strip()
        email = rh.email
        
        # Which fields are the user in?
        extras['from_user'] = False
        extras['to_user'] = False
        extras['cc_user'] = False
        
        # Get from_person only if he has an e-mail address
        if from_person and from_person.email:
            extras['from_person'] = from_person
        else:
            extras['from_person'] = None
        
        # To and CC with user removed
        extras['other_to'] = []
        extras['other_cc'] = []
        
        for to_person in to_persons:
            if (not to_person) or (not to_person.email):
                continue
            elif equivalent(name, email, to_person):
                extras['to_user'] = True
            else:
                extras['other_to'].append(to_person)
        
        for cc_person in cc_persons:
            if (not cc_person) or (not cc_person.email):
                continue
            elif equivalent(name, email, cc_person):
                extras['cc_user'] = True
            else:
                extras['other_cc'].append(cc_person)
        
        # All contacts not the user
        extras['all_others'] = extras['other_to'] + extras['other_cc']
        
        if extras['from_person']:
            if equivalent(name, email, from_person):
                extras['from_user'] = True
            else:
                extras['all_others'].append(from_person)

