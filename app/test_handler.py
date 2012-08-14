"""
Used to run tests from a running instance of the dev server -- useful to simulate
actual constraints of app engine. Borrows heavily from GAEUnit, but simplifies it
to returning only JSON results.

Also runs doctests.

Use with accompanying test.py in project root to run tests in the shell.

"""
import webapp2
import settings
import unittest
import time
import doctest
import simplejson as json


class JsonTestHandler(webapp2.RequestHandler):
    """
    Runs a specified test based on a "dotted name" that points to
    a module, test class, or function within that class
    """
    def get(self):
        # Don't want random users running tests during production mode
        assert settings.DEBUG
        
        # Get test
        test_name = self.request.get("name")
        loader = unittest.defaultTestLoader
        
        # Import as much as possible so loadTestsFromName can work
        split_name = test_name.split('.')
        mod_name = None
        for index, mod_name in enumerate(split_name):
            try:
                mod_name = '.'.join(split_name[:index+1])
                __import__(mod_name)
            except:
                mod_name = None
                break
        
        # Use unit loader to load test
        suite = loader.loadTestsFromName(test_name)
        
        # Also load doctests if applicable
        if mod_name:
            try:
                suite.addTest(doctest.DocTestSuite(module=mod_name))
            except ValueError: # Has no tests, ignore
                pass
        
        # Set up result object for rendering to JSON
        result = JsonTestResult()
        result.testNumber = suite.countTestCases()
        
        # Run actual test, time it
        start_time = time.time()
        suite(result)
        stop_time = time.time()
        result.time_taken = stop_time - start_time

        # Return result
        self.response.headers["Content-Type"] = "text/javascript"
        result.render_to(self.response.out)


class JsonTestResult(unittest.TestResult):
    """
    Subclass of unittest.TestResult that stores errors, results,
    etc., from test run.
    """
    def __init__(self):
        unittest.TestResult.__init__(self)
        self.testNumber = 0

    def render_to(self, stream):
        result = {
            'runs': self.testsRun,
            'total': self.testNumber,
            'errors': self._list(self.errors),
            'failures': self._list(self.failures),
        }
        if hasattr(self, 'time_taken'):
            result['time'] = self.time_taken
        stream.write(json.dumps(result))
    
    def _list(self, list):
        dict = []
        for test, err in list:
            d = { 
              'desc': test.shortDescription() or str(test), 
              'detail': err,
            }
            dict.append(d)
        return dict


app = webapp2.WSGIApplication([('/test', JsonTestHandler)],
                              debug=settings.DEBUG)
