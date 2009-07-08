#!/usr/bin/python
from urlparse import urlparse
import base64
import cStringIO
import datetime
import gzip
import httplib
import hmac
import md5
import sha
import mimetypes

__author__ = "Jeremy Carbaugh <jcarbaugh@sunlightfoundation.com>"
__version__ = "1.0"

TYPES_TO_COMPRESS = (
    "application/javascript",
    "application/x-javascript",
    "application/xml",
    "text/css",
    "text/html",
    "text/plain",
)

#
# actual doing stuff
#

def compress(s):
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
    zfile.write(s)
    zfile.close()
    return zbuf.getvalue()

def fetch(url):
    
    headers = {
        'User-Agent': 'url2s3.py - http://sunlightlabs.com',
    }
    
    uparts = urlparse(url)
    
    conn = httplib.HTTPConnection(uparts.netloc)
    conn.request("GET", uparts.path, None, headers)
    
    response = conn.getresponse()
    
    content = response.read()
    content_type = response.getheader('Content-Type', '')
    
    conn.close()
    
    return (content, content_type)

class S3(object):
    
    def __init__(self, key, secret, bucket):
        
        self._key = key
        self._secret = secret
        self._bucket = bucket
    
    def copy(self, from_url, to_keypath):
        
        # clean up keypath
        
        to_keypath = to_keypath.strip('/')
        
        # fetch content and check to see if content is compressable
        
        (content, content_type) = fetch(from_url)
        is_compressable = content_type.split(';')[0] in TYPES_TO_COMPRESS
        
        # generate needed date objects
        
        now = datetime.datetime.utcnow()
        rfc_now = now.strftime("%a, %d %b %Y %X GMT")
        expires = now + datetime.timedelta(1)

        # S3 connection
        
        s3_conn = httplib.HTTPConnection('s3.amazonaws.com')
        
        # compress content and generate checksum
        
        if is_compressable:
            content = compress(content)
        checksum = base64.b64encode(md5.new(content).digest())

        # create signature
        
        amz_headers = [
            "x-amz-acl:public-read",
            "x-amz-meta-source-url:%s" % from_url
        ]

        to_sign = "\n".join(["PUT", checksum, content_type, rfc_now, "\n".join(amz_headers), "/%s/%s" % (self._bucket, to_keypath)])
        sig = base64.encodestring(hmac.new(self._secret, to_sign, sha).digest()).strip()

        headers = {
            "x-amz-acl": "public-read",
            "x-amz-meta-source-url": from_url,
            "Expires": expires.strftime("%a, %d %b %Y %H:%M:%S UTC"),
            "Content-Type": content_type,
            "Content-Length": len(content),
            "Content-MD5": checksum,
            "Date": rfc_now,
            "Authorization": "AWS %s:%s" % (self._key, sig)
        }
        
        if is_compressable:
            headers["Content-Encoding"] = "gzip"

        s3_conn.request("PUT", "/%s/%s" % (self._bucket, to_keypath), content, headers)
        response = s3_conn.getresponse()
        s3_conn.close()
        
        if response.status != 200:
            print "Error: %s" % response.msg

if __name__ == '__main__':
    
    from optparse import OptionParser
    import sys
    
    # parse from rc file
    
    """ not completed """
    
    aws_key = None
    aws_secret = None
    
    # parse command line arguments
    
    usage = "usage: %prog [options] url bucket/keypath\nexample bucket/keypath: mybucket/path/to/file.txt"
    
    parser = OptionParser(usage=usage, version="%prog v" + __version__)
    parser.add_option("-k", "--awskey", action="store", dest="aws_key", default=aws_key,
                      help="AWS authentication key")
    parser.add_option("-s", "--awssecret", action="store", dest="aws_secret", default=aws_secret,
                      help="AWS authentication secret key")
                    
    (options, args) = parser.parse_args(sys.argv[1:])
    
    # parse arguments
    
    if len(args) != 2:
        parser.error("incorrect number of arguments")
    
    (from_url, bucket_keypath) = args
    
    bkparts = bucket_keypath.strip("/").split("/", 1)
    if len(bkparts) != 2:
        parser.error("invalid bucket/keypath")
    (bucket, keypath) = bkparts
    
    # check for required stuff
    
    if not options.aws_key:
        parser.error("AWS authentication key is required")
        
    if not options.aws_secret:
        parser.error("AWS authentication secret is required")
    
    # do s3 stuff
    
    s3 = S3(options.aws_key, options.aws_secret, bucket)
    s3.copy(from_url, keypath)