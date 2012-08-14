import webapp2
import datetime
import logging
import urllib
import helpers.jsond as json
from helpers.routing import url_for
from helpers.templates import render
from helpers.nested_dict import pset
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import users
from viz.models import VizData
import settings


def url_for_contact(contact):
    return url_for(ShowInfographic) + '?key=' + str(contact.viz_data_id)


class ShowInfographic(webapp2.RequestHandler):
    """
    Shows VizData for a contact
    """
    @login_required
    def get(self):
        viz_data_id = self.request.get('key')
        if not viz_data_id:
            self.error(404)
            return
        
        viz_data = VizData.get_by_id(long(viz_data_id))
        if not viz_data:
            self.error(404)
            return
        
        # Permission check
        user = users.get_current_user()
        fetching = viz_data.fetching
        if fetching.user != user:
            self.error(404)
            return
        
        # Rearrange data for compatability with template
        data = self.get_infographic_data(viz_data)
        
        # Share link
        data['share_link'] = share_url_for_viz_data(viz_data)
        
        # Render template
        if self.request.get('raw', None):
            rendered = json.dumps(data, sort_keys=True, indent=4)
            self.response.headers["Content-Type"] = "application/json"
        else:
            rendered = render('connected_html/infographic.html', data)
        self.response.out.write(rendered)
    
    def get_infographic_data(self, viz_data):
        """
        Tweak data to make compatible with template
        """
        data = json.loads(viz_data.json_data)
        fetching = viz_data.fetching
        user = fetching.user
        
        data.setdefault('from', {})
        data.setdefault('to', {})
        sort_hours(data)
        sort_months(data)
        add_to_from(data)
        
        data['contact'] = {
            'name' : viz_data.contact_name,
            'email' : viz_data.contact_email
        }
        you = data['you'] = {
            'name' : user.nickname(),
            'email' : user.email(),
            'num_emails' : fetching.num_emails,
            'num_to_emails' : fetching.num_to_emails,
            'num_from_emails' : fetching.num_from_emails,
            'avg_emails' : fetching.avg_emails,
            'avg_to_emails' : fetching.avg_to_emails,
            'avg_from_emails' : fetching.avg_from_emails
        }
        
        email_all = data['email_all']
        email_all['percentage'] = email_all['total_number']\
                                / float(you['num_emails'])
        email_all['to_percentage'] = email_all['total_to']\
                                   / float(you['num_to_emails'])
        email_all['from_percentage'] = email_all['total_from']\
                                     / float(you['num_from_emails'])
        email_all['relative'] = email_all['total_number']\
                              / float(you['avg_emails'])
        email_all['relative_to'] = email_all['total_to']\
                              / float(you['avg_to_emails'])
        email_all['relative_from'] = email_all['total_from']\
                              / float(you['avg_from_emails'])
        
        first_email = data.pop('first_email', None)
        if first_email:
            data['email_first'] = first_email
            email_dt = datetime.datetime.strptime(
                            first_email['date'],
                            "%Y-%m-%dT%H:%M:%S")
            delta = datetime.datetime.now() - email_dt
            first_email['days_ago'] = delta.days
            
            email_all['avg_per_day'] = email_all['total_number']\
                                     / float(delta.days)
            email_all['days_between_messages'] = 1\
                                               / email_all['avg_per_day']
        
        middle_email = data.pop('middle_email', None)
        if middle_email:
            data['email_middle'] = middle_email
            email_dt = datetime.datetime.strptime(
                            middle_email['date'],
                            "%Y-%m-%dT%H:%M:%S")
            delta = datetime.datetime.now() - email_dt
            middle_email['days_ago'] = delta.days
        
        last_email = data.pop('last_email', None)
        if last_email:
            data['email_last'] = last_email
            email_dt = datetime.datetime.strptime(
                            last_email['date'],
                            "%Y-%m-%dT%H:%M:%S")
            delta = datetime.datetime.now() - email_dt
            last_email['days_ago'] = delta.days
        
        return data

def sort_hours(contact_data):
    """
    Organizes emails per hour as a list of 24 items
    """
    from_hours_dict = contact_data['from'].pop('hour', {})
    to_hours_dict = contact_data['to'].pop('hour', {})
    
    from_hours_list = [0 for i in range(0,24)]
    for hour, count in from_hours_dict.items():
        hour = int(hour)
        from_hours_list[hour] = count
    
    to_hours_list = [0 for i in range(0,24)]
    for hour, count in to_hours_dict.items():
        hour = int(hour)
        to_hours_list[hour] = count
    
    total_hours_list = [(f + t) for f,t in
                        zip(from_hours_list, to_hours_list)]
    
    contact_data['num_emails_per_hour'] = total_hours_list
    contact_data['num_emails_to_contact_per_hour'] = to_hours_list
    contact_data['num_emails_from_contact_per_hour'] = from_hours_list

def sort_months(contact_data):
    """
    Organizes emails per month in a list of dicts
    """
    from_months_dict = contact_data['from'].pop('month', {})
    to_months_dict = contact_data['to'].pop('month', {})
    
    months = from_months_dict.keys() + to_months_dict.keys()
    months.sort()
    oldest_year, oldest_month, oldest_day = \
        [int(x) for x in months[0].split('-')]
    newest_year, newest_month, newest_day = \
        [int(x) for x in months[-1].split('-')]
    
    by_months_list = []
    for year, month in iter_month(oldest_year, oldest_month,
                                  newest_year, newest_month):
        str_key = str(datetime.date(year, month, 1))
        by_months_list.append({
            "Year" : year,
            "Month" : month,
            "From" : from_months_dict.get(str_key, 0),
            "To" : to_months_dict.get(str_key, 0)
        })
    
    contact_data['num_emails_to_from'] = by_months_list
    
def iter_month(start_year, start_month, end_year, end_month):
    """
    Iterates from start year-month to end year-month, inclusive.
    
    >>> for year, month in iter_month(2009, 11, 2011, 2):
    ...     print year, month
    2009 11
    2009 12
    2010 1
    2010 2
    2010 3
    2010 4
    2010 5
    2010 6
    2010 7
    2010 8
    2010 9
    2010 10
    2010 11
    2010 12
    2011 1
    2011 2
    
    """
    assert (end_year > start_year) or \
           (end_year == start_year and end_month >= start_month),\
        "Ending year-month must be greater than starting year-month"
    
    current_year = start_year
    current_month = start_month
    
    while (current_year < end_year) or \
          (current_year == end_year and current_month <= end_month):
        yield current_year, current_month
        
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

def add_to_from(contact_data):
    """
    Consolidate to / from counts
    """
    to_dict = contact_data.pop('to', {})
    total_to = to_dict.get('total', 0)
    pset(contact_data,
         ('email_all', 'total_to'),
         total_to)
    from_dict = contact_data.pop('from', {})
    total_from = from_dict.get('total', 0)
    pset(contact_data,
         ('email_all', 'total_from'),
         total_from)
    pset(contact_data,
         ('email_all', 'total_number'),
         total_to + total_from)


from fetching.util import requires_fetching
class ExportInfographic(webapp2.RequestHandler):
    @requires_fetching
    def get(self):
        if not users.is_current_user_admin():
            self.error(404)
            return
        
        offset = int(self.request.get("offset") or 0)
        contact_key = str(self.fetching.init_fetched_contacts[offset])
        viz_key_name = VizData.key_name_from(contact_key)
        viz_data = VizData.get_by_key_name(viz_key_name)
        
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(viz_data.json_data)


def share_url_for_viz_data(viz_data):
    return url_for(ShareInfographic) + '?' + urllib.urlencode({
                'key' : viz_data.key().id_or_name(),
                'check' : viz_data.share_key
           })


class ShareInfographic(ShowInfographic):
    def get(self):
        viz_data_id = self.request.get('key')
        if not viz_data_id:
            self.error(404)
            return
        
        # Get VizData
        viz_data = VizData.get_by_id(long(viz_data_id))
        if not viz_data:
            self.error(404)
            return
        
        # Permission check
        share_key = self.request.get('check') or ''
        if viz_data.share_key != share_key:
            self.error(404)
            return
        
        # Rearrange data for compatability with template
        data = self.get_infographic_data(viz_data)
        data['share_mode'] = True
        
        # Render template
        rendered = render('connected_html/infographic.html', data)
        self.response.out.write(rendered)
