#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import sys,os,re,datetime
from operator import attrgetter
import urlparse

from DocumentRepository import DocumentRepository
import Util
import LegalURI
from LegalRef import LegalRef, Link

__version__ = (0,1)
__author__  = u"Staffan Malmgren <staffan@tomtebo.org>"

class SKVFS(DocumentRepository):
    module_dir = "skvfs"

    # start_url = "http://www.skatteverket.se/rattsinformation/foreskrifter/tidigarear.4.1cf57160116817b976680001670.html"

    # This url contains slightly more (older) links (and a different layout)?
    start_url = "http://www.skatteverket.se/rattsinformation/lagrummet/foreskriftergallande/aldrear.4.19b9f599116a9e8ef3680003547.html"

    # also consolidated versions
    # http://www.skatteverket.se/rattsinformation/lagrummet/foreskrifterkonsoliderade/aldrear.4.19b9f599116a9e8ef3680004242.html
    
    # URL's are highly unpredictable. We must find the URL for every
    # resource we want to download, we cannot transform the resource
    # id into a URL
    def download_everything(self,cache=False):
        self.log.info("Starting at %s" % self.start_url)
        self.browser.open(self.start_url)
        years = {}
        for link in sorted(self.browser.links(text_regex=r'^\d{4}$'),
                           key=attrgetter('text')):
            year = int(link.text)
            url = link.absolute_url
            if year not in years:
                self.download_year(year,url)
                years[year] = url

    def download_new(self):
        self.log.info("Starting at %s" % start_url)
        self.browser.open(start_url)
        link = sorted(self.browser.links(text_regex=r'^\d{4}$'),
                        key=attrgetter('text'), reverse=True)[0]
        self.download_year(int(link.text),link.absolute_url, cache=True)

    def download_year(self, year, url, cache=False):
        self.log.info("Downloading year %s from %s" % (year, url))
        self.browser.open(url)
        for link in (self.browser.links(text_regex=r'FS \d+:\d+')):
            if "bilaga" in link.text:
                self.log.warning("Skipping attachment in %s" % link.text)
                continue
            
            # sanitize trailing junk
            linktext = re.match("\w+FS \d+:\d+", link.text).group(0)
            # something like skvfs/2010/23 or rsfs/1996/9
            basefile = linktext.strip().lower().replace(" ", "/").replace(":","/")
            self.download_single(basefile,link.absolute_url)

    def download_single(self, basefile, url, cache=False):
        self.log.info("Downloading %s from %s" % (basefile, url))
        self.document_url = url + "#%s"
        html_downloaded = super(SKVFS,self).download_single(basefile,cache)
        year = int(basefile.split("/")[1])
        if year >= 2007: # download pdf as well
            filename = self.downloaded_path(basefile)
            pdffilename = os.path.splitext(filename)[0]+".pdf"
            if not cache or not os.path.exists(pdffilename):
                soup = self.soup_from_basefile(basefile)
                pdflink = soup.find(href=re.compile(u'\.pdf$'))
                if not pdflink:
                    self.log.debug("No PDF file could be found")
                    return html_downloaded
                pdftext = Util.elementText(pdflink)
                pdfurl = urlparse.urljoin(url, pdflink['href'])
                self.log.debug("Found %s at %s" % (pdftext,pdfurl))
                pdf_downloaded = self.download_if_needed(pdfurl, pdffilename)
                return html_downloaded and pdf_downloaded
            else:
                return False
        else:
            return html_downloaded
        

if __name__ == "__main__":
    SKVFS.run()

        
