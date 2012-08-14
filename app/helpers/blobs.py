from google.appengine.api import files
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import login_required
import google.appengine.ext.blobstore as blobstore
from google.appengine.ext import db
from google.appengine.api import users
from helpers.routing import route, url_for


def store_blobs(content,
                mime_type='application/octet-stream',
                user=None):
    """
    Stores as blob, returns URL to access blob data
    Can restrict to a particular user
    """
    iterable = True
    if not hasattr(content, '__iter__'):
        iterable = False
        content = [content]
    permissions = []
    for c in content:
        file_name = files.blobstore.create(mime_type=mime_type)
        with files.open(file_name, 'a') as f:
            f.write(c)
        files.finalize(file_name)
        blob_key = files.blobstore.get_blob_key(file_name)
        permissions.append(UserBlobPermissions.make(user=user, blob=blob_key))
    
    url = url_for(ServeBlobHandler) + '?key='
    ret = [url + str(key) for key in db.put(permissions)]
    if iterable:
        return ret
    elif len(ret):
        return ret[0]
    else:
        return None


class UserBlobPermissions(db.Model):
    """
    Associate blob with an e-mail address to manage permissions
    """
    user = db.UserProperty()
    blob = blobstore.BlobReferenceProperty()
    
    @classmethod
    def make(cls, user, blob):
        if hasattr(blob, 'key') and callable(blob.key):
            blob = blob.key()
        key_name = str(blob)
        return cls(key_name=key_name, user=user, blob=blob)


class ServeBlobHandler(blobstore_handlers.BlobstoreDownloadHandler):
    # @login_required
    def get(self):
        ubkey = self.request.get('key')
        permissions = UserBlobPermissions.get(ubkey)
        # if permissions.user:
        #     if users.get_current_user() != permissions.user:
        #         self.error(403)
        self.send_blob(permissions.blob)


app = route([
    ('dl', ServeBlobHandler)
], prefix="files")
