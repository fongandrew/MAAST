from google.appengine.api import images
from helpers.nested_dict import pset
from helpers.blobs import store_blobs
from fetching.meta import MessageProcessor
from fetching.contacts import ContactProcessor
import traceback, sys
import settings
import re
import datetime
import logging

PHOTO_REGEX = re.compile(r'.*\.(jpe?g|gif|png|bmp)$', flags=re.I)
NUM_FIRST_PHOTOS = 3

class TrackPhotos(MessageProcessor):
    """
    Checks if message had any jpg, gif, bmp, or png attachments.
    """
    def __init__(self, *args, **kwds):
        self.data = {}
        super(TrackPhotos, self).__init__(*args, **kwds)
    
    def process(self, msg, extras={}):
        # See if there are any photos
        # Create 3-tuples of (date, file_name, file_id)
        files = []
        if msg.files: # msg.files is sometimes None
            for f in msg.files:
                # We're looking only for images that are bigger than
                # 1Kb (to weed out blinking smiley-face gifs and stuff)
                if PHOTO_REGEX.match(f.file_name) and f.size > 1000:
                    files.append((msg.date,
                                  f.file_name,
                                  msg.gmail_message_id,
                                  f.file_id))
        
        # Else, quit
        if not files: return
        
        for person in (extras.get('all_others') or []):
            self.handle_person(person, files)
    
    def handle_person(self, person, files):
        if person and person.email:
            data = self.data.setdefault(person.email, [])
            for f in files:
                data.append(f)
    
    def commit(self, extras={}):
        for email, file_list in self.data.iteritems():
            file_list.sort()
            pset(extras,
                 ('contact_data', email, 'first_photos'),
                 file_list[:settings.NUM_FIRST_PHOTOS])
            pset(extras,
                 ('contact_data', email, 'last_photos'),
                 file_list[0 - settings.NUM_FIRST_PHOTOS:])


class GetPhotos(ContactProcessor):
    """
    Retrieves photo from IMAP server via Context.IO
    """
    def imap_process(self, contact, data):        
        first_photos = data.get('first_photos', [])
        if first_photos:
            first_photos.sort()
            first_photos = first_photos[:settings.NUM_FIRST_PHOTOS]
        self.first_photos = first_photos
        
        last_photos = data.get('last_photos', [])
        if last_photos:
            last_photos.sort()
            last_photos = last_photos[0 - settings.NUM_LAST_PHOTOS:]
        self.last_photos = last_photos
        
        self.photo_data = {}
        for vals in (self.first_photos + self.last_photos):
            file_id = vals[-1]
            if file_id in self.photo_data:
                continue
            logging.debug("Fetching photo %s" % str(vals))
            try:
                self.photo_data[file_id] = self.account.get_file(file_id)
            except Exception, e:
                # Unble to get photo? Log and move on.
                logging.warning("Unable to retrieve photo - %s" % vals)
                info = "".join(traceback.format_tb(sys.exc_info()[2]))
                logging.warning(info)
                logging.warning(str(e))
    
    def post_process(self, contact, data):
        # Resize - we can always redirect user to gmail if they
        # want the larger image. And then store as a blob.
        
        # Different dimensions for each photo
        self.store_and_resize(self.first_photos, 0, width=395, height=238)
        self.store_and_resize(self.first_photos, 1, width=190, height=113)
        self.store_and_resize(self.first_photos, 2, width=190, height=113)
        self.store_and_resize(self.last_photos, 0, width=160, height=238)
        self.store_and_resize(self.last_photos, 1, width=100, height=115)
        self.store_and_resize(self.last_photos, 2, width=100, height=115)
        
        data['first_photos'] = self.first_photos
        data['last_photos'] = self.last_photos
    
    def store_and_resize(self, lst, index, width, height):
        if len(lst) <= index:
            return
        file_date, file_name, gmail_message_id, file_id = lst[index]
        content = self.photo_data[file_id]
        
        try:
            img = images.Image(content)
            # These resizings are somewhat convoluted but I'm tired.
            # Will simply later. Maybe.
            if img.width > width and img.height > height:
                des_ratio = float(width) / float(height)
                img_ratio = float(img.width) / float(img.height)
                if des_ratio > img_ratio:
                    img.resize(width=width)
                    new_height = width / img_ratio
                    crop_y = ((new_height - height) / 2.0) / new_height
                    img.crop(
                        top_y=crop_y,
                        bottom_y=(1-crop_y),
                        left_x=0.0,
                        right_x=1.0
                    )
                else:
                    img.resize(height=height)
                    new_width = height * img_ratio
                    crop_x = ((new_width - width) / 2.0) / new_width
                    img.crop(
                        top_y=0.0,
                        bottom_y=1.0,
                        left_x=crop_x,
                        right_x=(1-crop_x)
                    )
            else:
                img.resize(width=img.width) # Do nothing, but "transform"
                                            # so we can convert to JPG
            img = img.execute_transforms(output_encoding=images.JPEG)
        
        except Exception, e:
            # Something's wrong with the image
            # Log and move on. Store content as is.
            img = content
            logging.warning("Unable to process photo id %s" % file_id)
            info = "".join(traceback.format_tb(sys.exc_info()[2]))
            logging.warning(info)
            logging.warning(str(e))
        
        lst[index] = {
            'url' : store_blobs([img], mime_type='image/jpeg')[0],
            'gmail_message_id' : gmail_message_id,
            'file_name' : file_name,
            'date' : file_date
        }
