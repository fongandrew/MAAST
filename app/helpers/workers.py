"""
Base class for task workers
"""
from google.appengine.api import taskqueue
from helpers.routing import url_for
import webapp2

class TaskWorker(webapp2.RequestHandler):
    """
    A class that represents a request that works in the background.
    Assumes this worker has been connected using the route function
    in helpers.routing.
    """
    def post(self):
        raise NotImplementedError(
            "This is an abstract base class. "
            "Do not use directly.")
    
    def get(self):
        raise NotImplementedError(
            "This is a task worker function. "
            "Do not call with GET method.")
    
    @classmethod
    def add_task(cls, params={}, **kwds):    
        """
        Adds a task corresponding to this class (or a subclass).
        
        params : Dict of params to pass this task.
        kwds : Other values passed to taskqueue.add
        
        """
        kwds['params'] = params
        kwds['url'] = url_for(cls)
        return taskqueue.add(**kwds)

    