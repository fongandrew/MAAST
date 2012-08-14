#!/usr/bin/env python
import urllib, urllib2
import sys
import os
import argparse
import decimal
import re
import copy

# Import json library from Google App Engine lib
current_path = os.path.abspath(os.path.dirname(__file__))
json_path = os.path.join(current_path, 'gae', 'lib', 'simplejson')
sys.path.append(json_path)
import simplejson as json


# Default variables
# This is the default address of the app engine dev server.
DEFAULT_TEST_ADDRESS = 'http://localhost:8080/test'
DEFAULT_OUTPUT = sys.stdout
DEFAULT_ERROR = sys.stderr
DEFAULT_RELATIVE_TO = os.path.join(os.path.dirname(__file__), 'app')
DEFAULT_EXCLUDE = [
    'lib',
    'settings',
    'test_handler'
]


def run_named_test(name, address):
    """
    Calls dev server, asks it to run a given test and gets
    JSON-encoded results of test.
    """
    # Try to contact server
    data = urllib.urlencode({'name' : name})
    try:
        response = urllib2.urlopen(address + '?' + data)
    except urllib2.URLError: # Unable to reach server, quit.
        return None
    except urllib2.HTTPError: # 500 or 404?
        return False
    
    # Translate response from server into Python objects
    if response.getcode() == 200:
        # Success!
        # Assume data is JSON and read.
        data = json.loads(response.read())
    else:
        # 500 error from server or related.
        # Record error and output as is.
        data = {
            'failures' : [],
            'errors' : [{
                'detail' : 'response.read()',
                'desc' : name,
            }],
            'total' : 1,
            'runs' : 0,
            'time' : 0
        }
    
    # Return Python object
    return data


def run_named_tests(names,              # List of dotted names
        output=DEFAULT_OUTPUT,          # Stream to output to
        error=DEFAULT_ERROR,            # Error stream
        address=DEFAULT_TEST_ADDRESS,   # Test server address
        **kwargs):
    """
    Runs through all named tests passed as arguments.
    Prints out fairly verbose test details. May want to add
    more options later.
    """ 
    # Aggregate test info
    all_responses = []
    total_tests = 0
    total_errors = 0
    total_failures = 0
    total_time = 0
    
    # Gather test data for everything, printing some preliminary
    # responses so user knows something is happening
    output.write('\n')
    for name in names:
        # Print out name of test
        output.write(name + " ... ")
        
        # Run against dev server
        data = run_named_test(name, address)
        
        if data: # Some response from server
            
            # Update aggregate info
            num_errors = len(data['errors'])
            num_failures = len(data['failures'])
            num_tests = data['total']
            time_elapsed = data['time']
            total_errors += num_errors
            total_failures += num_failures
            total_tests += num_tests
            total_time += time_elapsed
            all_responses.append(data)
            
            # Print something
            if data['runs']:
                output.write('E' * num_errors)
                output.write('F' * num_failures)
                output.write('*' * (num_tests - num_errors - num_failures))
                output.write(' (%s seconds)' % fmt_float(time_elapsed))
            else:
                output.write('no tests')
            output.write('\n')
        
        elif data is False: # Error code. We're done.
            output.write("X\n")
            error.write("Test server error. "
                        "Check test server logs for details.")
            sys.exit(-1)
        
        else: # No response means unable to contact server. We're done.
            output.write("X\n")
            error.write("ERROR: Unable to contact test server. "
                        "Please make sure dev server is running "
                        "and reachable at %s. \n\n" % address)
            sys.exit(-1)
            
    
    # Print details of errors and failures
    for response in all_responses:
        for item in (response['errors'] + response['failures']):
            output.write('\n')
            output.write(item['desc'])
            output.write('\n------------------------------------------------------------\n')
            output.write(item['detail'])
            output.write('\n')
        
    # Print aggregate data
    output.write('------------------------------------------------------------\n')
    output.write("%s tests: %s errors, %s failures.\n" % 
                 (total_tests, total_errors, total_failures))
    output.write("%s seconds elapsed during testing.\n\n"
                  % fmt_float(total_time))


def fmt_float(flt):
    "Returns float as 3-digit decimal"
    return decimal.Decimal(flt).quantize(decimal.Decimal('1.000'))


def discover(path='', exclude=[], relative_to=''):
    """
    Returns "dotted names" for all python modules under a given path,
    recursively searching within packages to return modules inside.
    
    exclude: list of packages and module names to not search within,
             should consist of dotted names
             
    relative_to: path is relative to this variable. Should be filepath.
                 Returned modules will be returned relative to this
                 variable, which should be within sys.path of the
                 test/dev server. If blank, everything is relative to
                 current working directory.
    
    """
    results = []
    search_pattern = re.compile(r'.+\.py$')
    
    # We only want names relative to a certain path
    if relative_to:
        path = os.path.join(relative_to, path)
    
    # All results returned by os.walk include full path
    # We just want things relative to that, so get length
    # of this so we can remove.
    prepend = len(relative_to)
    if not relative_to.endswith('/'):
        prepend += 1
    
    # os.walk does recursive walking over file structure
    for dirpath, dirnames, filenames in os.walk(path):
        
        # Remove excluded directories
        to_remove = []
        for dn in dirnames:
            dn = os.path.join(dirpath, dn)
            dn = dn[prepend:]
            dotted_name = path_to_dotted_name(dn)
            if dotted_name in exclude:
                # don't remove right away so iteration doesn't get screwed up
                to_remove.append(dotted_name)
                exclude.remove(dotted_name)
        for tr in to_remove:
            dirnames.remove(tr)
        
        # Verify current directory is a reachable package
        if '__init__.py' in filenames or path.startswith(dirpath):
            
            # List all files that match .py pattern
            for fn in filenames:
                if search_pattern.match(fn):
                    fn = os.path.join(dirpath, fn)
                    fn = fn[prepend:]
                    dotted_name = path_to_dotted_name(fn)
                    
                    # Ignore excluded files
                    if dotted_name in exclude:
                        exclude.remove(dotted_name)
                    else:
                        results.append(dotted_name)
        
        else: # Exclude all subdirectories
            dirnames_copy = copy.copy(dirnames)
            for dn in dirnames_copy:
                dirnames.remove(dn)
    
    return results


def path_to_dotted_name(path):
    """
    Converts "/path/to/file.py" to something like path.to.file
    Assumes you're being good and don't have package or module names
    with periods and spaces in them.
    """
    if path.endswith('.py'):
        path = path[:0 - len('.py')]
    if path.endswith('__init__'):
        path = path[:0 - len('__init__')]
    path = path.replace('/', '.').replace('\\',  '.')
    if path.endswith('.'):
        path = path[:-1]
    if path.startswith('.'):
        path = path[1:]
    return path


def main(names, relative_to, exclude, **kwargs):
    """
    Given a list of names, or lack thereof, construct appropriate
    dotted names we can pass to test server. Then print out results.
    
    relative_to: Which file path are names relative to
    
    exclude: Absent names, which paths should we not search
    
    kwargs: Includes things like server
    
    """    
    # For each dotted name, determine if we're looking at a
    # package or something else
    test_names = []
    for dotted_name in names:
        
        # Determine if package by looking for __init__.py
        split_name = dotted_name.split('.')
        path = os.path.join(*split_name)
        pkg_init_name = os.path.join(relative_to, path, '__init__.py')
        if os.access(pkg_init_name, os.F_OK):
            test_names += discover(path, relative_to=relative_to)
        
        else: # Must be something else
            test_names.append(dotted_name)
    
    if not test_names: # use defaults
        test_names = discover('',
            exclude=exclude,
            relative_to=relative_to)
    
    # Actual run
    run_named_tests(names=test_names, **kwargs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('names', metavar='name', type=str, nargs='*',
                        help='"Dotted names" of tests to run')
    parser.add_argument('--address',
                        default=DEFAULT_TEST_ADDRESS,
                        help="Test server address")
    parser.add_argument('--relative_to', default=DEFAULT_RELATIVE_TO,
                        help="Which directory are packages relative to")
    parser.add_argument('--exclude', nargs='*', default=DEFAULT_EXCLUDE,
                        help="Which dotted names to exclude")
    
    namespace = parser.parse_args()
    main(**vars(namespace))
