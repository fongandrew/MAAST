"""
Functional test to make sure index page is OK
"""
import unittest
from lib import webtest
from helpers.testing import Testbed

from index import app


class TestIndex(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_user_stub()
        # App to send responses to
        self.app = webtest.TestApp(app)
    
    def tearDown(self):
        self.testbed.deactivate()
    
    def test_index_before_login(self):
        response = self.app.get('/')
        self.assertEqual(response.status, "302 Moved Temporarily")
        
    def test_index_after_login(self):
        self.testbed.login_as()
        response = self.app.get('/')
        self.assertEqual(response.status, "200 OK")
    

