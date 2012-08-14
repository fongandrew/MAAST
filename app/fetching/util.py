from functools import wraps
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import users
from fetching.models import Fetching
from helpers.routing import url_for

def requires_fetching(func):
    @wraps(func)
    @login_required
    def get_fetching(self, *args, **kwds):
        user = users.get_current_user()
        fetching = Fetching.get_most_recent(user.email())
        if not fetching:
            from fetching.manage import FirstLoginHandler
            self.redirect(url_for(FirstLoginHandler))
            return
        self.fetching = fetching
        return func(self, *args, **kwds)
    return get_fetching
    