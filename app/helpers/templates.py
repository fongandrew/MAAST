import settings
import jinja2
import os
import datetime

environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(settings.TEMPLATES_DIR))

def render(name, context={}):
    """
    Shortcut function to get a template by name and render
    it with some set of given values.
    """
    template = environment.get_template(name)
    
    # Auto add designated constants from settings
    # Prepend with underscore to prevent name conflicts
    for constant in settings.TEMPLATE_CONSTANTS:
        namespaced_constant = '_' + constant
        
        # Sanity check - we shouldn't be passing context vars to
        # render that are going to be overwritten by this method.
#        if namespaced_constant in context:
#            raise ValueError("Context vars should not start with underscore.")
        
        context[namespaced_constant] = getattr(settings, constant)
    
    # Set some other vars for debugging purposes
    template.globals['context'] = get_context
    template.globals['repr'] = repr
    template.globals['to_datetime'] = to_datetime
    
    return template.render(context)

@jinja2.contextfunction
def get_context(c):
    "Returns context as is -- for debugging purposes"
    return c
    
def to_datetime(s):
    "Convert str to datetime obj"
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    
    
import webapp2
class TestRender(webapp2.RequestHandler):
    template = ''
    vars = {}
    def get(self):
        assert self.template, "Template must be set!"
        rendered = render(self.template, self.vars)
        self.response.out.write(rendered)
