"""
Basics for connecting with Context.IO
"""

from google.appengine.api import users
from google.appengine.ext import db
from lib.contextIO2 import ContextIO, Account
from helpers.workers import TaskWorker
from fetching.models import FetchTask, Fetching
import webapp2
import settings
import logging
import hashlib

class ContextIOMeta(type):
    def __new__(cls, name, bases, attrs):        
        old_get = attrs.get('get', None)
        if old_get:
            def new_get(self, *args, **kwds):
                if self.setup_context_io():
                    return old_get(self, *args, **kwds)
            attrs['get'] = new_get
        
        old_post = attrs.get('post', None)
        if old_post:
            def new_post(self, *args, **kwds):
                if self.setup_context_io():
                    return old_post(self, *args, **kwds)
            attrs['post'] = new_post
        
        return super(ContextIOMeta, cls).__new__(cls, name, bases, attrs)


class ContextIOBase(webapp2.RequestHandler):
    """
    Base class for below request handlers
    """
    TIMEOUT = 30
    
    __metaclass__ = ContextIOMeta
    
    def post(self):
        raise NotImplementedError(
            "This is an abstract base class. "
            "Do not use directly.")
    
    def get(self):
        raise NotImplementedError(
            "This is an abstract base class. "
            "Do not use directly.")
    
    def setup_context_io(self, email):
        """
        Creates Context.IO client to access a given account
        Returns account object.
        """
        self.email = email
        
        context_io = ContextIO(
            consumer_key=settings.API_KEY,
            consumer_secret=settings.API_SECRET,
            timeout=self.TIMEOUT)
        self.context_io = context_io
        
        account_list = context_io.get_accounts(email=email)
        assert len(account_list) >= 1, \
            "%s not found in Context.io mailboxes" % email
        self.account = account_list[0]
        return self.account
    
    def get_source(self):
        if getattr(self, 'source', None):
            return self.source
        sources = self.account.get_sources()
        assert sources, "Account has no sources"
        self.source = sources[0]
        return self.source
        
    def get_label(self):
        if getattr(self, 'label', None):
            return self.label
        source = self.get_source()
        label = source['label']
        assert label, "Account source unlabeled"
        self.label = label
        return label
    
    def get_sync_data(self):
        """
        Gets the last sync time for this account, both start and stop
        """
        # get_sync() not implemented in Context.IO yet apparently
        # So grab it semi-manually
        return self.account.request_uri(
                    'sources/%s/sync' % self.get_label(),
                    method="GET")
    
    def get_last_sync(self):
        """
        Gets the last sync-start time for this account.
        We use sync start because that indicates the latest possible time of
        the most recent message synced to Context.IO.
        """
        sync_data = self.get_sync_data()
        return int(sync_data.values()[0]['last_sync_start'])
    
    def initial_import_finished(self):
        """
        Returns True if Context.IO has finished syncing with IMAP account
        """
        sync_data = self.get_sync_data()
        return int(sync_data.values()[0]['initial_import_finished'])


class WorkerMeta(ContextIOMeta):
    def __new__(cls, name, bases, attrs):        
        old_post = attrs.get('post', None)
        if old_post:
            def new_post(self, *args, **kwds):
                self.on_start()
                ret = old_post(self, *args, **kwds)
                self.complete()
                return ret
            attrs['post'] = new_post
        
        return super(WorkerMeta, cls).__new__(cls, name, bases, attrs)


class ContextIOWorker(ContextIOBase, TaskWorker):
    """
    Base class for worker requests that need to talk to Context.IO
    """  
    TIMEOUT = 500
    
    __metaclass__ = WorkerMeta
    
    @classmethod
    def add_task(cls, fetching_key, params=None, unique=False, **kwds):    
        """
        Adds a task corresponding to this class (or a subclass).
        
        fetching_key : A key for a Fetching object. All task requests to
                       Context.IO should be done in the context of
                       a fetching object.
        params : Dict of params to pass this task.
        unique : By default, set to True. Keyword only. If True, will not
                 create a task if another task with the same combination
                 of fetching_key and params exist.
        
        """
        params = params or {}
        if 'fetching_key' in params:
            params.pop('fetching_key')
        if not isinstance(fetching_key, db.Key):
            fetching_key = db.Key(fetching_key)
        
        key_name = cls.task_key_name(fetching_key, **params)
        if unique: # Create unique FetchTask -- quit otherwise
            def txn():
                entity = FetchTask.get_by_key_name(
                            key_name,
                            parent=fetching_key)
                if entity:
                    return False
                return FetchTask(key_name=key_name,
                                 parent=fetching_key,
                                 **params).put()
            ft_key = db.run_in_transaction(txn)
            if not ft_key:
                logging.warning("Unable to add task with params %s" % str(params))
                return False
            params['fetch_task_key'] = str(ft_key)
        
        params['fetching_key'] = str(fetching_key)
        return super(ContextIOWorker, cls).add_task(params=params, **kwds)
    
    # Names for a combination of params that, when in a given combination,
    # with params and class name, should not yield more than one task.
    UNIQUE_PARAM_SET = []
    
    @classmethod
    def task_key_name(cls, fetching_key, **params):
        """
        This function should return string that ensures task uniqueness
        and ability to check task completion. Uses fetching_key plus
        values in unique_param_set.
        
        """        
        unique_set = {}
        unique_set['fetching_key'] = str(fetching_key)
        unique_set['__class__'] = str(cls.__name__)
        
        for param in cls.UNIQUE_PARAM_SET:
            val = str(params.get(param, ''))
            if val == '0' or val == 'None':
                val == ''
            unique_set[param] = val
        
        items = unique_set.items()
        items.sort()
        return hashlib.sha256(str(items)).hexdigest()        
    
    def get_fetch_task(self):
        if not hasattr(self, '_fetch_task'):
            params = {}
            for arg in self.request.arguments():
                val = self.request.get_all(arg)
                # Convert lists to single items
                if len(val) == 1:
                    val = val[0]
                params[arg] = val
            key_name = self.__class__.task_key_name(**params)
            self._fetch_task = FetchTask.get_by_key_name(key_name,
                                    parent=self.fetching_key)
        return self._fetch_task
    
    def on_start(self):
        """
        Make a note that the task has started and store it.
        Creates programmatic way of identifying and splitting
        up problematic tasks
        """
        ft = self.get_fetch_task()
        if ft:
            ft.fetch_task_tries += 1
            ft.put()
    
    def complete(self):
        """
        Call to signal task completion
        """
        ft = self.get_fetch_task()
        if ft:
            ft.complete = True
            ft.put()
    
    def setup_context_io(self):
        """
        Pull e-mail from request to do set up
        """
        # Get fetching key, fetching object, and fetch task (if it exists)
        self.fetching_key = db.Key(self.request.get('fetching_key'))
        self.fetching = Fetching.get(self.fetching_key)
        assert self.fetching, "Invalid fetching key supplied"
        
        ft_key = self.request.get('fetch_task_key')
        if ft_key:
            self.fetch_task_key = db.get(ft_key)
        else:
            self.fetch_task_key = None
        
        self.email = self.fetching.email        
        self.user = self.fetching.user            
        return super(ContextIOWorker, self).setup_context_io(self.email)
    
    def replicate(self, params={}, **kwds):
        """
        Adds this task to the queue again with the same
        params, except with the specified params changed
        
        """
        # Get old params -- NB: haven't really tested this with lists
        # and multiple args passed to a key
        for arg in self.request.arguments():
            # If passed, used new params
            if arg in params:
                continue
            # Else, grab old ones
            old_val = self.request.get_all(arg)
            # Convert lists to single items
            if len(old_val) == 1:
                old_val = old_val[0]
            params[arg] = old_val
        
        fetching_key = params.pop('fetching_key')\
                           or self.fetching_key
        return self.__class__.add_task(fetching_key,
            params=params, **kwds)


class ContextIORequest(ContextIOBase):
    """
    For use with non-worker / front-end facing classes
    """
    TIMEOUT = 30
    
    def setup_context_io(self):
        """
        Sets up context.IO for current user, returns account object.
        Returns false means redirect required or error
        """
        # Make sure user is logged in
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return False
        self.user = user
        
        # Get context.IO info, or redirect
        email = user.email().lower()
        try:
            return super(ContextIORequest, self).setup_context_io(email)
        except AssertionError:
            nickname = user.nickname()
            names = nickname.split()
            first_name = ' '.join(names[:-1])
            last_name = ' '.join(names[-1:])
            ret = self.context_io.post_connect_token(self.request.url,
                email=email, first_name=first_name, last_name=last_name)
            redirect_addr = str(ret['browser_redirect_url'])
            self.redirect(redirect_addr)
            return False



 
    