"""
Fetches meta-data (basically, everything except the body) for all e-mails
in a user's inbox. Avoids expensive IMAP calls.

"""
from fetching.base import ContextIOWorker
import logging, time
import settings

class FetchCountWorker(ContextIOWorker):
    """
    Gets and sets total number of e-mails,
    as well as sync period.
    
    """    
    @classmethod
    def add_task(cls, *args, **kwds):
        # Doesn't have to be unique (multiple counts = more
        # overhead, but not a bad thing), so pass that along
        # to avoid unnecessary locking.
        kwds['unique'] = False
        kwds['queue_name'] = 'init'
        return super(FetchCountWorker, cls).add_task(*args, **kwds)
    
    def post(self):
        """
        Expects the following request params
        
        fetching_key - key for the entity representing this fetching
        
        """
        num_emails = self.get_num_emails()
        assert num_emails, "Sync not started yet"
        
        self.fetching.num_emails = num_emails
        self.fetching.timing = self.get_last_sync()
        self.fetching.put()
        
    def get_num_emails(self):
        """
        Ask Context.IO for email count. This should be fairly accurate
        as it's an IMAP call and not subject to Context.IO syncing.
        
        """
        # Get list of folders
        folders = self.account.request_uri(
            'sources/%s/folders' % self.get_label(),
            method="GET", params={'include_extended_counts' : '1'})
        
        # Go over list of returned folders
        # Look for "[Gmail]/All Mail" or, failing that, the folder with
        # the highest count (which should be "all mail").
        counts = []
        for folder in folders:
            num = folder.get('nb_messages', 0)
            if folder.get('name') == "[Gmail]/All Mail":
                return num
            counts.append(num)
        if counts:
            return max(counts)
        else:
            return None


class FetchMetaWorker(ContextIOWorker):
    """
    FetchMetaWorker fetches the metadata for messages from Context.IO.
    FetchMetaWorker will replicate itself in a rate-limited manner to
    fetch all the messages it can.
    
    """
    UNIQUE_PARAM_SET = ['offset', 'init_finished', 'limit', 'index_before', 'index_after']
    
    @classmethod
    def add_task(cls, *args, **kwds):
        # Potential for workers to run in parallel, and if they fail
        # they may try to recreate each other, so must be unique
        kwds['unique'] = True
        kwds['queue_name'] = 'messages'
        kwds['target'] = 'messages'
        return super(FetchMetaWorker, cls).add_task(*args, **kwds)
    
    def post(self):
        """
        Called as task worker -- checks for following params ...
        
        fetching_key - Fetching key (required)
        offset - Where to start grabbing messages
                 If blank, start with 0
        max_messages - When replicating, offset+limit should be < this
                       number. If blank, goes through all messages.
        limit - How many messages to fetch
                If blank, use settings.BATCH_LIMIT
        init_finished - Has Context.IO finished initial import?
                        If no value supplied, defaults to empty string.
        index_before - Only fetch messages indexed before this date
                       Seconds since epoch. If blank, default to
                       10 seconds ago.
        index_after - Only fetch messages indexed after this date
                      Seconds since epoch. If blank, fetch all.
        
        """
        # logging.debug("Meta start @ %s" % time.time())
        
        # Load ContextIO query params
        index_before = int(float(self.request.get('index_before')
                           or (time.time() - 10)))
        index_after = int(self.request.get('index_after')
                          or 1)
        
        offset = int(self.request.get('offset')
                     or 0)
        limit = int(self.request.get('limit') 
                    or settings.BATCH_LIMIT)
        init_finished = bool(self.request.get('init_finished')
                             or False)
        
        # Enforce max on messages to process
        max_messages = int(self.request.get('max_messages')
                           or 0)
        if max_messages:
            limit = min(limit, max_messages - offset)
            if limit <= 0:
                return # We're done
        
        # Check if we've done this before
        ft = self.get_fetch_task()
        if ft and ft.fetch_task_tries > 1:
            # If so, likely cause for previous failure is memory overload
            # or some very problematic task. Split up into smaller batches.
            if limit > settings.SMALLER_BATCH_LIMIT:
                params = {
                    'limit' : settings.SMALLER_BATCH_LIMIT,
                    'max_messages' : offset + limit, 
                }
                self.replicate(params=params)
                return # Let replicated tasks handle this
            
            # If we get here, we've previously failed despite
            # smaller batch sizes. Let things go and raise
            # an error in the logs.
        
        # Go get some messages
        messages = self.account.get_messages(indexed_after=index_after,
                                             indexed_before=index_before,
                                             offset=offset,
                                             limit=limit)
        
        # logging.debug("Finished fetching messages @ %s" % time.time())
        
        # Before we process messages, create worker to fetch
        # additional messages, if there are any
        num_messages = len(messages)
        
        # We know there are no more messages to fetch if we've previously
        # received notice that the initial sync has finished and we've
        # retreived fewer messages than we asked for
        done = init_finished and num_messages < limit
        
        # Else, create worker to fetch additional messages
        if not done:
            
            # No messages at all? Let's check if the initial sync has
            # finished. Regardless, we should do one more check to
            # verify that no messages came in between our last fetch
            # and our last initial sync check.
            if not num_messages:
                init_finished = self.initial_import_finished()
            
            # Create new worker with incremented params
            params = {
                'offset' : offset + num_messages,
                'index_before' : index_before,
                'init_finished' : ('1' if init_finished else ''),
            }
            if num_messages == 0:
                params['index_before'] = int(time.time() - 10)
                params['index_after'] = int(index_before + 1)
                params['offset'] = 0
            self.replicate(params=params)
        
        # Now we can process messages
        # Run processors on all messages
        self.process_all(messages)
        
        # logging.debug("Meta done @ %s" % time.time())
    
    def process_all(self, messages):
        """
        Calls all processors for a given message
        """
        # This is where processors are listed
        # Make sure they're loaded
        import processors.register
        
        # Instantiate all processor classes
        processors = []
        for processor_cls in self.processor_clses:
            processor = processor_cls(self)
            processor.time_used = 0
            processors.append(processor)
        
        # Iterate through all messages
        # logging.debug("Start message processing @ %s" % time.time())
        for message in messages:
            extras = {}
            for processor in processors:
                # start = time.time()
                processor.process(message, extras)
                # end = time.time()
                # processor.time_used += (end - start)
                if extras.get('STOP_PROCESSING'):
                    break
        
        # for processor in processors:
        #     logging.debug("%s processor took %s seconds" % 
        #         (processor.__class__.__name__, processor.time_used))
                
        # commit anything saved by processors
        extras= {}
        for index, processor in enumerate(processors):
            logging.debug("Process %s commit start @ %s" %
                (processor.__class__.__name__, time.time()))
            processor.commit(extras)
            
            # Remove references to reduce memory use
            del processor
            processors[index] = None
    
    @classmethod
    def register_processor(cls, func):
        """
        Call to register a processor that will process a message. Each processor
        should be a subclass of MessageProcessor (below).
        
        """
        if not func in cls.processor_clses:
            cls.processor_clses.append(func)
            return True
    processor_clses = []


class MessageProcessor(object):
    """
    Base class for a callable that handles a message
    """
    def __init__(self, request_handler):
        """
        Initialize with reference to request handler
        """
        self.request_handler = request_handler
    
    def process(self, message, extras={}):
        """
        Handles a message, or instance of a Context.IO Message object
        Also, takes a dict of "extras" that get passed from processor
        to processor.
        
        """
        raise NotImplementedError(
            "Abstract class requires handle be defined")
    
    def commit(self, extras={}):
        """
        What happens after all messages have been handled for a
        given fetch? This functions gets called to commit results
        to a database in a transactional call, etc. We move logic
        here to minimize the number of transactional rights we
        need to do.
        
        """
        pass

def register_processor(func):
    FetchMetaWorker.register_processor(func)
