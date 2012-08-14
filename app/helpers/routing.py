"""
Helper functions to assist with URL routing

>>> class TestHandler(webapp2.RequestHandler):
...     def get(self):
...         pass
>>> class TestHandler2(webapp2.RequestHandler):
...     def get(self):
...         pass

>>> url_for(TestHandler) # doctest: +ELLIPSIS
Traceback (most recent call last):
    ...
UnassignedHandlerException: ...

>>> app = route(prefix="cat", routes=[
...     ('test', TestHandler),
...     ('test2', TestHandler2)
... ])
>>> for r in app.app.router.match_routes:
...     print r # doctest: +ELLIPSIS
<...'/cat/test', <...TestHandler...>
<...'/cat/test2', <...TestHandler2...>

>>> url_for(TestHandler)
'/cat/test'
>>> url_for(TestHandler2)
'/cat/test2'

"""
import settings
import webapp2

ROUTES = {}

def route(routes, prefix=''):
    """
    Takes a list of 2-tuples of paths + webapp2 RequestHandlers.
    Optionally takes a prefix to prepend to each URL.
    
    Returns a webapp2.WSGIApplication.
    
    """
    if not prefix.startswith('/'):
        prefix = '/' + prefix
    if not prefix.endswith('/'):
        prefix = prefix + '/'
    for index, route in enumerate(routes):
        path, handler = route
        if path.startswith('/'):
            path = path[1:]
        path = prefix + path
        urls = urls_for(handler)
        urls.append(path)
        routes[index] = (path, handler)
    
    return webapp2.WSGIApplication(routes, debug=settings.DEBUG)

def url_for(instance):
    """
    Takes instance of RequestHandler (or RequestHandler class itself)
    and returns first known URL / path for this handler. Raises
    UnassignedHandlerException if no URL found.
    """
    urls = urls_for(instance)
    if not urls:
        raise UnassignedHandlerException("No path assigned to this handler")
    return urls[0]

class UnassignedHandlerException(Exception):
    """
    Exception for when we try to retreive a url for handler
    that hasn't been assigned one
    """
    pass

def urls_for(instance):
    """
    Takes instance of RequestHandler (or RequestHandler class itself)
    and returns list of URLs / paths for this handler
    """
    if isinstance(instance, webapp2.RequestHandler):
        instance = instance.__class__
    urls = ROUTES.get(instance, None)
    if urls is None: # Create dict if unassigned
        urls = []
        ROUTES[instance] = urls
    return urls
