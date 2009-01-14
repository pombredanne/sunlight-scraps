'''
    Grab a listing of all Your Seat at the Table documents from change.gov

    James Turk <jturk@sunlightfoundation.com>
    14 January 2009

'''
import urllib
import csv
import os.path
import re
from BeautifulSoup import BeautifulSoup

BASE_URL = 'http://change.gov/open_government/yourseatatthetable/'

def get_num_pages():
    html = urllib.urlopen(BASE_URL).read()
    soup = BeautifulSoup(html)
    paginate = soup.find('p', {'class': 'paginate'}).contents[0]
    num_pages = re.match('Page 1 of (\d*)', paginate).groups()[0]
    return int(num_pages)

def gen_filenames(max_page):
    base = BASE_URL + 'P%d0/'
    for n in xrange(max_page):
        yield base % n

def get_pdf_links(html):
    soup = BeautifulSoup(html)
    return [link for link in soup.findAll('a') 
            if link.get('href', '').endswith('.pdf')]

def build_csv(filename):
    out = csv.writer(open(filename,'w'))
    num_pages = get_num_pages()
    for url in gen_filenames(num_pages):
        data = urllib.urlopen(url).read()
        for pdflink in get_pdf_links(data):
            nameblock = pdflink.parent.parent.find('strong')
            titleblock = pdflink.parent.parent.find('p')
            title = titleblock.contents[0] if titleblock else '?'
            name = nameblock.contents[0] if nameblock else '?'
            link = pdflink['href']
            if link.startswith('/http'):
                link = link[1:]
            if link.startswith('/page/'):
                link = 'http://change.gov' + link
            out.writerow((name,title,link))

def download_files(filename, dest_dir):
    reader = csv.reader(open(filename))
    for line in reader:
        link = line[2]
        fname = os.path.join(dest_dir, link.split('/')[-1])
        if not os.path.exists(fname):
            urllib.urlretrieve(link, fname)

if __name__ == '__main__':
    # this runs for a while as it has to hit > 100 pages
    build_csv('yourseat.csv')

    # careful, this takes a long time and is > 1GB of downloads
    #download_files('yourseat.csv', 'pdfs')
