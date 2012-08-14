def clean_str(s):
    """
    Fix up string for storage in App Engine StringProperty
    
    """
    s = s or ''
    if not isinstance(s, basestring):
        s = str(s)
    s = s[:500]
    s = s.replace('\n', '').replace('\r', '')
    return s
