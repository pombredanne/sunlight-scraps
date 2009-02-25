""" Python library for interacting with the GOP.gov Anywhere API
"""

__author__ = "James Turk (jturk@sunlightfoundation.com)"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2009 Sunlight Labs"
__license__ = "BSD"

import urllib, urllib2

class GopApiError(Exception):
    """ Exception for GOP.gov API errors """

# namespaces 
class gop(object):

    apikey = None 

    @staticmethod
    def _apicall(method, **params):
        if gop.apikey is None:
            raise GopApiError('Missing GOP.gov api key')

        url = 'http://www.gop.gov/api/%s' % method
        params['api_token'] = gop.apikey
        body = urllib.urlencode(params)
        return urllib2.urlopen(url, body).read()

    
    class member(object):

        @staticmethod
        def getall():
            result = gop._apicall('member.getall')
            return result

        @staticmethod
        def get(state, district):
            result = gop._apicall('member.get', member_state=state, 
                                  member_district=district)
            return result

        @staticmethod
        def group(state='', rssurl=None, gender=None, active=None):

            if rssurl:
                member_rssurl = 'yes'
            elif rssurl is None:
                member_rssurl = ''
            else:
                member_rssurl = 'no'

            if active:
                member_status = 'active'
            elif active is None:
                member_status = ''
            else:
                member_status = 'retired'

            result = gop._apicall('member.group', member_state=state,
                                  member_rssurl=member_rssurl,
                                  member_gender=gender,
                                  member_status=member_status)
            return result

    class committee(object):

        @staticmethod
        def getall():
            pass

        @staticmethod
        def members():
            pass

    class legdigest(object):
        @staticmethod
        def getall():
            pass

        @staticmethod
        def get():
            pass

    class bill(object):
        @staticmethod
        def getall(congress):
            result = gop._apicall('bill.getall', bill_congress=congress)
            return result

        @staticmethod
        def get(bill_number, congress):
            result = gop._apicall('bill.get', bill_number=bill_number,
                                  bill_congress=congress)
            return result

        @staticmethod
        def keyword():
            pass

        @staticmethod
        def committee():
            pass

    class vote(object):
        @staticmethod
        def getall():
            pass

        @staticmethod
        def get(roll, session, congress):
            result = gop._apicall('vote.get', vote_roll=roll, 
                                  vote_session=session, vote_congress=congress)
            return result

        @staticmethod
        def member(roll, congress, state, district):
            result = gop._apicall('vote.member', vote_roll=roll, 
                                  vote_congress=congress, member_state=state,
                                  member_district=district)
            return result

    class docs(object):
        @staticmethod
        def getall():
            pass

        @staticmethod
        def get():
            pass

        @staticmethod
        def keyword():
            pass

        @staticmethod
        def committee():
            pass
