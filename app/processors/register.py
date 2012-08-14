# List all processors here -- this will be loaded by the fetching function
# This is for meta / message processing
from fetching.meta import register_processor as register_meta

from processors.user_id import UserID
register_meta(UserID)

from processors.create_contacts import CreateContact
register_meta(CreateContact) 

from processors.contact_counts import CountContactMsg
register_meta(CountContactMsg)

from processors.first_last_email import TrackFirstLastEmail
register_meta(TrackFirstLastEmail)

from processors.photos import TrackPhotos
register_meta(TrackPhotos)

from processors.words import CountWordsProcessor
register_meta(CountWordsProcessor)

from processors.awesome import AwesomeValuationProcessor
register_meta(AwesomeValuationProcessor)

from processors.longest_thread import TrackThreadContactProcessor
register_meta(TrackThreadContactProcessor)

# This should be registered after anything that
# gets contact-specific data to be stored in JSONCounts
from processors.json_counts import StoreContactCounts
register_meta(StoreContactCounts)

# These next processors are not currently reversible.
# Call near the end, so if one of the earlier ones
# screw up, we don't get double counting.
from processors.latest_loaded import SaveFetchedMsg
register_meta(SaveFetchedMsg)

from processors.total_counts import CountMsg
register_meta(CountMsg)

from processors.total_contact_counts import CountContactProcessor
register_meta(CountContactProcessor)


#############################################


# This is for contact / post processing
from fetching.contacts import register_processor as register_contact

# This goes first so we can retrieve JSON data for other post processing
from processors.json_counts import GetContactCounts
register_contact(GetContactCounts)

from processors.contact_counts import ProcessContactMsg
register_contact(ProcessContactMsg)

from processors.first_last_email import GetFirstLastEmail
register_contact(GetFirstLastEmail)

from processors.photos import GetPhotos
register_contact(GetPhotos)

from processors.words import GetWordCountsProcessor
register_contact(GetWordCountsProcessor)

from processors.longest_thread import SortThreadsProcessor
register_contact(SortThreadsProcessor)

from processors.awesome import AwesomeCutoffProcessor
register_contact(AwesomeCutoffProcessor)
