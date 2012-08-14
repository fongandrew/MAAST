"""
Helpers functions for testing
"""
from google.appengine.ext import testbed
from google.appengine.api import users
import uuid

class Testbed(testbed.Testbed):
    """
    Drop in replacement for standard testbed with some additional functions
    """
    def login_as(self, id=None, email=None, nickname=None, admin=0):
        """
        Creates stub user to login as
        
        Test without Testbed call
        
        >>> users.get_current_user() is None
        True
        
        Now test using testbed
        
        >>> tb = Testbed()
        >>> tb.activate()
        >>> tb.init_user_stub()
        >>> tb.login_as()
        >>> users.get_current_user() #doctest: +ELLIPSIS
        users.User(...)
        >>> tb.deactivate()
        
        """
        id = id or str(uuid.uuid4())
        self.setup_env(user_id=id, overwrite=True)
        
        email = email or (id.replace('-','') + '@example.com')
        self.setup_env(user_email=email, overwrite=True)
        
        nickname = nickname or id
        self.setup_env(user_nickname=nickname, overwrite=True)
        
        self.setup_env(auth_domain='example.com', overwrite=True)
        self.setup_env(user_is_admin=str(admin), overwrite=True)
        
        reload(users)
 
        

