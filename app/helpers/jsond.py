"""
Version of JSON decoder than handle datetime and sets

>>> import datetime
>>> dt = datetime.datetime(2012,4,19,1,1,1)
>>> dumps({'dt' : dt})
'{"dt": "2012-04-19T01:01:01"}'
>>> dumps(set([5]))
'[5]'

"""
import json

def encoder(obj):
    if isinstance(obj, set):
        return list(obj)
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return json.dumps(obj)
    
def dumps(obj, **kwds):
    default = kwds.pop('default', encoder)
    return json.dumps(obj, default=default, **kwds)

from json import loads