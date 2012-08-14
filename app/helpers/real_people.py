"""
Code to identify real people and who's identical to a user
"""
import re
import logging


EMAIL_BLACKLIST = [
    re.compile(r'.*\b(wallmaster|notifications?|confirm|photos)\b'
               r'.*@facebook(mail)?\.com', flags=re.I),
    re.compile(r'no\W*reply\W', flags=re.I),
    re.compile(r'('
        r'admin|'
        r'automailer|'
        r'bot|'
        r'contact|'
        r'feedback|'
        r'help|'
        r'info|'
        r'mail'
    r')[@+-]', flags=re.I),
    re.compile(r'.*\bnotification.*\b@.*', flags=re.I),
]

EMAIL_WHITELIST = [
    re.compile(
        r'.*?@('
            r'(gmail|hotmail|yahoo)\.com'
        r'|.*?\.edu)',
    flags=re.I),
]

NAME_BLACKLIST = [
    re.compile(r'('
        r'Facebook\b|'
        r'Groupon\b|'
        r'Amazon\b|'
        r'Twitter\b|'
        r'iTunes\b|'
        r'Apple\s*$'
    r')', flags=re.I)
]

def real_person(contact):
    """
    Returns true if contact appears to be a real person and not a bot
    
    contact - Something with name and email properties
    
    >>> class Contact(object):
    ...     pass
    
    >>> fb1 = Contact()
    >>> fb1.name = 'Facebook'
    >>> fb1.email = 'something@facebook.com'
    >>> real_person(fb1)
    False
    
    >>> fb2 = Contact()
    >>> fb2.name = ''
    >>> fb2.email = 'notification+fl1lfe6z@facebookmail.com'
    >>> real_person(fb1)
    False
    
    >>> bl1 = Contact()
    >>> bl1.name = ''
    >>> bl1.email = 'bob@loblaw.com'
    >>> real_person(bl1)
    True
    
    >>> aw = Contact()
    >>> aw.name = 'Apple Williams'
    >>> aw.email = 'apple@gmail.com'
    >>> real_person(aw)
    True
    
    """
    name = contact.name
    email = contact.email
    
    if not email:
        return False
    
    # Check whitelist
    for regex in EMAIL_WHITELIST:
        if regex.match(email):
            return True
    
    # Check blacklists
    if name:
        for regex in NAME_BLACKLIST:
            if regex.match(name):
                return False
    
    for regex in EMAIL_BLACKLIST:
        if regex.match(email):
            return False
    
    return True
    

def equivalent(user_name, user_email, contact):
    """   
    Returns true if user is equivalent to given contact
    
    user_name - Name of user
    user_email - Email address of user
    contact - Something with name and email properties
    
    Create some stubs
    
    >>> class Contact(object):
    ...     pass
    
    >>> bob1 = Contact()
    >>> bob1.name = 'Bob Loblaw'
    >>> bob1.email = 'bob@loblaw.com'
    
    >>> bob2 = Contact()
    >>> bob2.name = 'Bobert Loblaw'
    >>> bob2.email = 'bobloblaw@yahoo.com'
    
    >>> job = Contact()
    >>> job.name = 'Job Bluth'
    >>> job.email = 'job@bluth.com'
    
    >>> equivalent('Bob Loblaw', 'bobloblaw@gmail.com', bob1)
    True
    >>> equivalent('Bob Loblaw', 'bobloblaw@gmail.com', bob2)
    True
    >>> equivalent('Bob Loblaw', 'bobloblaw@gmail.com', job)
    False
    
    """
    # Break down name and address for processing
    contact_email = contact.email.lower()
    contact_username = contact_email.split('@')[0]
    contact_name = contact.name or ''
    contact_name = contact_name.lower()
    contact_name = contact_name.replace(',',' ')
    contact_names = contact_name.split()
    contact_names = [name for name in contact_names if name]
    
    username = user_email.split('@')[0]
    simplified_username = username.replace('.','')\
                                  .replace('-','')\
                                  .replace('_','')
    user_names = user_name.replace(',','').split()
    user_names = [name.lower() for name in user_names if name]
    
    # Identical email? Call it a day.
    if user_email == contact_email:
        return True
    
    # Check for identical names
    if set(user_names) == set(contact_names):
        return True
    
    # Now check for similar e-mail addresses.
    # In the unlikely event you got something like jane@gmail.com
    # don't automatically exclude jane@hotmail.com.
    # But otherwise, if you have janedoe29@gmail.com, exclude
    # janedoe29@hotmail.com.
    if (user_names and user_names[0] != simplified_username
              and simplified_username == contact_username):
        return True
    
    return False
