#!/usr/bin/env python

# Copyright (c) 2009, James Turk
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# * Neither the name of James Turk, Sunlight Foundation, Sunlight Labs
# nor the names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
    Dependencies:
        python 2.5
        lxml
        selenium
"""

from subprocess import Popen
import time
from csv import DictWriter
from urllib2 import urlopen
from lxml.html import fromstring, parse

def get_index():
    '''
        use Selenium to access search result page

        Selenium script is as follows:
            Under "Documents To Search." select Both Under Opportunity/Procurement Type
            Select "Awards"
            Under " Recovery and Reinvestment Act Action." select Yes
    '''
    from selenium import selenium
    sel = selenium("localhost", 4444, "*chrome", "http://fbo.gov/")

    # follow script
    sel.start()
    sel.open("/?s=opportunity&tab=search&mode=list")
    sel.click("dnf_class_values_procurement_notice__procurement_type___a_check")
    sel.click("yui-gen4")
    sel.click("yui-gen5")
    sel.click("//form[@id='vendor_procurement_notice_search']/div/div[3]/input[1]")
    sel.wait_for_page_to_load("30000")

    # hack to avoid dealing with pagination, increase pp to 10000
    sel.open('https://www.fbo.gov/?&s=opportunity&mode=list&tab=searchresults&tabmode=list&pp=10000')

    # get source & turn of server
    html = sel.get_html_source()
    sel.shut_down_selenium_server()
    return html

def parse_index(html, filename):
    '''
        Parse fbo.gov search results page and all opportunity pages.
    '''
    base_url = 'https://www.fbo.gov/index'
    mapping = {'title': '.agency-header h2',
     'agencies': '.agency-name',
     'sol_num': '#dnf_class_values_procurement_notice__solicitation_number__widget',
     'award_date': '#dnf_class_values_procurement_notice__contract_award_date__widget',
     'award_num': '#dnf_class_values_procurement_notice__contract_award_number__widget',
     'award_amount': '#dnf_class_values_procurement_notice__contract_award_amount__widget',
     'contractor_name': '#dnf_class_values_procurement_notice__contractor_awarded_name__widget',
     'contractor_address': '#dnf_class_values_procurement_notice__contractor_awarded_address__widget',
     'synopsis': '#dnf_class_values_procurement_notice__description__widget',
     'contracting_office_address': '#dnf_class_values_procurement_notice__office_address__widget',
     'place_of_performance': '#dnf_class_values_procurement_notice__place_of_performance__widget',
     'primary_point_of_contact': '#dnf_class_values_procurement_notice__primary_poc__widget',
     'original_posted_date': '#dnf_class_values_procurement_notice__original_posted_date__widget',
     'posted_date': '#dnf_class_values_procurement_notice__posted_date__widget',
     'classification_code': '#dnf_class_values_procurement_notice__classification_code__widget',
     'naics_code': '#dnf_class_values_procurement_notice__naics_code__widget'}
    outfile = DictWriter(open(filename, 'w'), mapping.keys())

    # write csv header
    outfile.writerow(dict(zip(mapping.keys(), mapping.keys())))

    # follow all links to awards
    for link in fromstring(html).cssselect('.lst-lnk-notice'):
        url = base_url + link.attrib['href']
        print url
        doc = parse(urlopen(url)).getroot()

        # map inner text of css elements to fields
        record = {}
        for name,css in mapping.iteritems():
            elements = doc.cssselect(css)
            if not elements:
                # if element is missing try and get the archived version
                css.replace('_notice__', '_notice_archive__')
                elements = doc.cssselect(css)

            # assign stripped inner text to row or log that the data was missing
            if len(elements) == 1:
                record[name] = elements[0].text_content().encode('ascii', 'ignore').strip()
            else:
                print '    ',name
        outfile.writerow(record)

def main():
    '''
        create CSV of fedbizopps data
    '''
    print 'starting selenium server...'
    selenium_server = Popen('java -jar /home/james/bin/selenium/selenium-server.jar', shell=True)
    time.sleep(3)   # give the server time to start
    print 'automating browser to download index...'
    html = get_index()
    print 'downloading contract data...'
    parse_index(html, 'fedbizopps.csv')

if __name__ == '__main__':
    main()
