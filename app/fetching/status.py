from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext import db
import webapp2
import datetime
from helpers.templates import render
from helpers.routing import url_for
import helpers.jsond as json
from fetching.models import Fetching, FetchTask, FetchedContact
from fetching.util import requires_fetching
from processors.latest_loaded import FetchedMessage
from processors.total_counts import MessageCounter
import logging


class StatusPage(webapp2.RequestHandler):
    """
    Get loading page of fetch for current user
    """
    @requires_fetching
    def get(self):
         # If we're done, redirect to completion page
        if self.fetching.viz_complete:
            from main import ListContacts
            self.redirect(url_for(ListContacts))
            return
        
        self.response.out.write(
            render("loading.html", {
                'status_url' : url_for(StatusData)
            })
        )
        

class StatusData(webapp2.RequestHandler):
    """
    Returns JSON dict with data about current fetch
    
    """
    @requires_fetching
    def get(self):
        # Get current Fetching object or redirect to start page
        fetching = self.fetching
        
        # Get recent messages too
        messages = FetchedMessage.all()\
                                 .filter('fetching =', fetching)\
                                 .order('date')\
                                 .fetch(10)
        messages = [{
            'gmail_message_id' : msg.gmail_message_id,
            'from' : {
                'email' : str(msg.from_email),
                'name' : msg.from_name
            },
            'to' : [{ 'email' : str(email),
                      'name' : name } 
                    for email, name
                     in zip(msg.to_emails, msg.to_names)],
            'subject' : msg.subject,
            'date' : msg.date
        } for msg in messages]
        
        # Get count of processed essages
        processed_count = MessageCounter.total(
                            fetching_key=fetching.key())
        
        response = {
            'email' : fetching.email,
            'total_messages' : fetching.num_emails or 0,
            'messages_processed' : processed_count,
            'messages' : messages,
            'viz_complete' : fetching.viz_complete,
            'meta_complete' : fetching.meta_complete,
        }
        
        # Get (a) contact we're currently fetching
        if fetching.init_fetched_contacts:
            q = FetchTask.all()\
                         .ancestor(fetching)\
                         .filter('complete =', False)
            ft = q.fetch(1)
            try:
                offset = int(ft[0].offset)
            except:
                offset = None
            if offset:
                if len(fetching.init_fetched_contacts) > offset:
                    contact = fetching.init_fetched_contacts[offset]
                    contact = FetchedContact.get(contact)
                    response['current_contact'] = {
                        'number' : offset,
                        'name' : contact.name,
                        'email' : contact.email
                    }
        
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(json.dumps(response))


class TestStatusPage(webapp2.RequestHandler):
    """
    Get loading page of fetch for current user
    """
    def get(self):
        self.response.out.write(
            render("loading.html", {
                'status_url' : url_for(TestStatusData)
            })
        )


class TestStatusData(webapp2.RequestHandler):
    """
    Returns JSON dict with data about current fetch
    
    """
    def get(self):
        # Get recent messages too
        messages = [{
            'gmail_message_id' : "11ce4a8d0c5066bf",
            'from' : {
                'email' : 'jane.foster@example.com',
                'name' : 'Jane Foster'
            },
            'to' : [{ 'email' : 'id@andrewfong.com',
                      'name' : 'Andrew Fong' }],
            'subject' : "This weekend at my place - Blue Angels and house concert",
            'date' : datetime.datetime(2008, 10, 8, 14, 22, 42)
        }]
        
        response = {
            'email' : 'id@andrewfong.com',
            'total_messages' : 125387,
            'messages_processed' : 73142,
            'messages' : messages,
            'viz_complete' : False,
            'meta_complete' : False,
        }
        
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(json.dumps(response))
