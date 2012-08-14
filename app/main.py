"""
Main user-facing request handlers
"""
import webapp2
import cgi
from fetching.models import FetchedContact
from fetching.util import requires_fetching
from google.appengine.ext import db
from fetching.manage import FirstLoginHandler
from google.appengine.api import users
from helpers.routing import route, url_for
from helpers.templates import render
from viz.views import url_for_contact, \
                      ShowInfographic, \
                      ExportInfographic, \
                      ShareInfographic, \
                      VizData
import hashlib, urllib, os
import settings


class IndexPage(webapp2.RequestHandler):
    """
    Main index page
    """
    def get(self):
        template = 'connected_html/index.html'
        current_user = users.get_current_user()
        if current_user:
            current_user.name = current_user.nickname() or current_user.email()
        rendered = render(template, {
            'users' : current_user
        })
        self.response.out.write(rendered)


class InvitationCode(db.Model):
    """
    Represents invitation codes
    """
    #code
    code = db.StringProperty(required=True)
    
    #Has this code been used?
    used = db.BooleanProperty(default=False)


class PasswordPage(webapp2.RequestHandler):
    """
    Invitation Code page
    """
    def get(self):
        template = 'connected_html/password.html'
        rendered = render(template)      
        self.response.out.write(rendered)
        
    def post(self):
        code_correct = False
        template = 'connected_html/password.html'
        code = cgi.escape(self.request.get('code'))
        email = cgi.escape(self.request.get('email'))
        
        #see if this is a correct code
        if code != "" and code != "your 6 digit code":
          que = InvitationCode.gql("WHERE code= :1", code)
          result = que.fetch(limit=1)        
          if len(result) > 0:
            if result[0].used == False:
              code_correct = True
        
        #master code
        if code == "1masta":
          code_correct = True
          
        error_msg = ""
        email_msg = ""
        
        if code_correct == True:
          #this code has been used now
          if code != "1masta":
            result[0].used = True
            result[0].put()
          self.redirect("/contacts")
        else:
          error_msg = "You entered a wrong code."
        
        if email != "" and email !="your email address":
          email_msg = "Thank you! We will let you know shortly!"  
          
        rendered = render(template, {
          'error_msg': error_msg,
          'email_msg': email_msg
        })
        
      
        self.response.out.write(rendered)
        

class ListContacts(webapp2.RequestHandler):
    """
    List contacts for a given user once fetched
    """
    @requires_fetching
    def get(self):
        # If we're not done, redirect to completion page
        if not self.fetching.viz_complete:
            from fetching.status import StatusPage
            self.redirect(url_for(StatusPage))
            return
        
        # Get variables for rendering
        template = 'connected_html/contacts.html'
        current_user = users.get_current_user()
        if current_user:
            current_user.name = current_user.nickname() or current_user.email()
        
        # Get initial / top contacts
        contacts = FetchedContact.get(
                        self.fetching.init_fetched_contacts)
        # In case FetchedContact has been purged
        if (not contacts) or (None in contacts):
            query = VizData.all().filter("fetching =", self.fetching)
            contacts = query.fetch(10)
            for contact in contacts:
                contact.name = contact.contact_name
                contact.email = contact.contact_email
                contact.viz_data_id = str(contact.key().id_or_name())
        
        rendered = render(template, {
            'users' : current_user,
            'contacts' : [{
                'name_or_email' : contact.name or contact.email.split('@')[0],
                'photo' : photo_for(contact),
                'emails' : contact.total_emails,
                'url' : url_for_contact(contact)
            } for contact in contacts]
        })
        self.response.out.write(rendered)

def photo_for(contact):
    """
    Returns a correctly sized gravatar photo or our default
    """
    if os.environ.get('HTTP_HOST'): 
        host = os.environ['HTTP_HOST'] 
    else: 
        host = os.environ['SERVER_NAME'] 
    
    default = 'http://' + host + settings.DEFAULT_PHOTO
    email = contact.email
    size = 96
    gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
    return gravatar_url


# URL routing goes here 
app = route([
    ('/', IndexPage),
    ('/password', PasswordPage),
    ('/contacts', ListContacts),
    ('/infographic', ShowInfographic),
    ('/infographic/export', ExportInfographic),
    ('/infographic/share', ShareInfographic)
])

