from fetching.manage import FirstLoginHandler,\
                            FetchCompletionWorker
from fetching.meta import FetchMetaWorker,\
                          FetchCountWorker
from fetching.contacts import FetchForContactWorker
from fetching.status import StatusPage,\
                            StatusData,\
                            TestStatusPage,\
                            TestStatusData
from helpers.routing import route


app = route([
    ('meta', FetchMetaWorker),
    ('count', FetchCountWorker),
    ('start', FirstLoginHandler),
    ('status', StatusPage),
    ('status/data', StatusData),
    ('status/test', TestStatusPage),
    ('status/data/test', TestStatusData),
    ('complete', FetchCompletionWorker),
    ('contacts', FetchForContactWorker)
], prefix="fetch")

