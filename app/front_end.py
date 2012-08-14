import webapp2
from helpers.templates import TestRender
import settings

# Copy and paste the class below to create new test page
class Index(TestRender):
    template = 'connected_html/index.html'
    vars = {}

class Contacts(TestRender):
    template = 'connected_html/contacts.html'
    vars = {
        'user' : {'name' : 'Ariel'},
        'contacts' : [{
            'name_or_email' : 'Bob Loblaw',
            'photo' : 'http://localhost:8080/static/img/contact_thumb/NoPhoto.gif',
            'emails' : 100,
            'url' : '/infographic?key=1'
        }, {
            'name_or_email' : 'Ariel Loblaw',
            'photo' : 'http://localhost:8080/static/img/contact_thumb/NoPhoto.gif',
            'emails' : 200,
            'url' : '/infographic?key=2'
        }, {
            'name_or_email' : 'Bob Loblaw',
            'photo' : 'http://localhost:8080/static/img/contact_thumb/NoPhoto.gif',
            'emails' : 100,
            'url' : '/infographic?key=3'
        }, {
            'name_or_email' : 'Bob Loblaw',
            'photo' : 'http://localhost:8080/static/img/contact_thumb/NoPhoto.gif',
            'emails' : 100,
            'url' : '/infographic?key=4'
        }, {
            'name_or_email' : 'Monica Loblaw',
            'photo' : 'http://localhost:8080/static/img/contact_thumb/NoPhoto.gif',
            'emails' : 100,
            'url' : '/infographic?key=5'
        }, {
            'name_or_email' : 'Bob Loblaw',
            'photo' : 'http://localhost:8080/static/img/contact_thumb/NoPhoto.gif',
            'emails' : 100,
            'url' : '/infographic?key=6'
        }, {
            'name_or_email' : 'Bob Loblaw',
            'photo' : 'http://localhost:8080/static/img/contact_thumb/NoPhoto.gif',
            'emails' : 100,
            'url' : '/infographic?key=7'
        }, {
            'name_or_email' : 'Andrew Loblaw',
            'photo' : 'http://localhost:8080/static/img/contact_thumb/NoPhoto.gif',
            'emails' : 100,
            'url' : '/infographic?key=8'
        }, {
            'name_or_email' : 'Bob Loblaw',
            'photo' : 'http://localhost:8080/static/img/contact_thumb/NoPhoto.gif',
            'emails' : 100,
            'url' : '/infographic?key=9'
        }, {
            'name_or_email' : 'Seba Loblaw',
            'photo' : 'http://localhost:8080/static/img/contact_thumb/NoPhoto.gif',
            'emails' : 100,
            'url' : '/infographic?key=10'
        }]
    }

class Infographic(TestRender):
    template = 'connected_html/infographic.html'
    vars = {
      'num_emails_per_hour':[704,716,102,708,672,610,566,317,550,536,120,576,422,395,418,251,156,143,131,276,240,473,570,633],
      'num_emails_to_from':
      [{"Year":2008,"Month":1,"From":1,"To":3},
      {"Year":2008,"Month":2,"From":2,"To":3},
      {"Year":2008,"Month":3,"From":5,"To":4},
      {"Year":2008,"Month":4,"From":4,"To":5},
      {"Year":2008,"Month":5,"From":12,"To":13},
      {"Year":2008,"Month":6,"From":12,"To":13},
      {"Year":2008,"Month":7,"From":6,"To":7},
      {"Year":2008,"Month":8,"From":9,"To":12},
      {"Year":2008,"Month":9,"From":10,"To":11},
      {"Year":2008,"Month":10,"From":12,"To":14},
      {"Year":2008,"Month":11,"From":8,"To":11},
      {"Year":2008,"Month":12,"From":5,"To":8},
      {"Year":2009,"Month":1,"From":3,"To":4},
      {"Year":2009,"Month":2,"From":23,"To":6},
      {"Year":2009,"Month":3,"From":1,"To":6},
      {"Year":2009,"Month":4,"From":5,"To":1},
      {"Year":2009,"Month":5,"From":2,"To":1},
      {"Year":2009,"Month":6,"From":4,"To":2},
      {"Year":2009,"Month":7,"From":4,"To":2},
      {"Year":2009,"Month":8,"From":2,"To":2},
      {"Year":2009,"Month":9,"From":6,"To":3},
      {"Year":2009,"Month":10,"From":7,"To":1},
      {"Year":2009,"Month":11,"From":3,"To":5},
      {"Year":2009,"Month":12,"From":2,"To":1},
      {"Year":2010,"Month":1,"From":14,"To":15},
      {"Year":2010,"Month":2,"From":12,"To":14},
      {"Year":2010,"Month":3,"From":14,"To":15},
      {"Year":2010,"Month":4,"From":14,"To":16},
      {"Year":2010,"Month":5,"From":8,"To":10},
      {"Year":2010,"Month":6,"From":10,"To":11},
      {"Year":2010,"Month":7,"From":9,"To":11},
      {"Year":2010,"Month":8,"From":14,"To":16},
      {"Year":2010,"Month":9,"From":19,"To":21},
      {"Year":2010,"Month":10,"From":19,"To":21},
      {"Year":2010,"Month":11,"From":16,"To":18},
      {"Year":2010,"Month":12,"From":9,"To":10},
      {"Year":2011,"Month":1,"From":16,"To":17},
      {"Year":2011,"Month":2,"From":14,"To":15},
      {"Year":2011,"Month":3,"From":4,"To":4},
      {"Year":2011,"Month":4,"From":1,"To":2},
      {"Year":2011,"Month":5,"From":2,"To":1},
      {"Year":2011,"Month":6,"From":7,"To":7},
      {"Year":2011,"Month":7,"From":12,"To":4},
      {"Year":2011,"Month":8,"From":11,"To":9},
      {"Year":2011,"Month":9,"From":10,"To":5},
      {"Year":2011,"Month":10,"From":10,"To":4},
      {"Year":2011,"Month":11,"From":2,"To":1},
      {"Year":2011,"Month":12,"From":3,"To":4}]
    }

# Assign test page URLs here
pages = [
    ('/', Index),
    ('/contacts', Contacts),
    ('/infographic', Infographic),
]

# Don't change this
app = webapp2.WSGIApplication(pages, debug=settings.DEBUG)
