#2023-03-20
# edit 2025-09-14

import re
from resources.lib.control import getSetting, urljoin
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser
from resources.lib.utils import isBlockedHoster

SITE_IDENTIFIER = 'serienstream'
SITE_DOMAIN = 'serienstream.to'
SITE_NAME = SITE_IDENTIFIER.upper()

class source:
    def __init__(self):
        self.priority = 2
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = '/serien'
        self.sources = []

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        aLinks = []
        if season == 0: 
            return self.sources
        try:
            t = [cleantitle.get(i) for i in titles if i]
            url = urljoin(self.base_link, self.search_link)
            oRequest = cRequestHandler(url)
            oRequest.cacheTime = 60*60*24*7
            sHtmlContent = oRequest.request()

            links = dom_parser.parse_dom(sHtmlContent, "div", attrs={"class": "genre"})
            links = dom_parser.parse_dom(links, "a")
            links = [(i.attrs["href"], i.content) for i in links]

            for i in links:
                for a in t:
                    try:
                        if any([a in cleantitle.get(i[1])]):
                            aLinks.append({'source': i[0]})
                            break
                    except:
                        pass

            if len(aLinks) == 0: 
                return self.sources

            for i in aLinks:
                url = i['source']
                self.run2(url, year, season=season, episode=episode, hostDict=hostDict, imdb=imdb)
        except:
            return self.sources
        return self.sources

    def run2(self, url, year, season=0, episode=0, hostDict=None, imdb=None):
        try:
            url = url[:-1] if url.endswith('/') else url
            if "staffel" in url:
                url = re.findall("(.*?)staffel", url)[0]
            url += '/staffel-%d/episode-%d' % (int(season), int(episode))
            url = urljoin(self.base_link, url)
            sHtmlContent = cRequestHandler(url).request()

            a = dom_parser.parse_dom(sHtmlContent, 'a', attrs={'class': 'imdb-link'}, req='href')
            foundImdb = a[0].attrs["data-imdb"]
            if not foundImdb == imdb: 
                return

            lr = dom_parser.parse_dom(sHtmlContent, 'div', attrs={'class': 'hosterSiteVideo'})
            r = dom_parser.parse_dom(lr, 'li', attrs={'data-lang-key': re.compile('[1]')})  # nur deutsch
            if r == []: 
                r = dom_parser.parse_dom(lr, 'li', attrs={'data-lang-key': re.compile('[1|2|3]')})

            r = [(i.attrs['data-link-target'], dom_parser.parse_dom(i, 'h4'),
                  'subbed' if i.attrs['data-lang-key'] == '3' else '' if i.attrs['data-lang-key'] == '1' else 'English/OV' if i.attrs['data-lang-key'] == '2' else '') for i in r]
            r = [(i[0], re.sub('\s(.*)', '', i[1][0].content), 
                  'HD' if 'hd' in i[1][0][1].lower() else 'SD', i[2]) for i in r]

            for link, host, quality, info in r:
                quality = 'HD'  # temp
                isBlocked, hoster, url, prioHoster = isBlockedHoster(host, isResolve=False)
                if isBlocked: 
                    continue
                self.sources.append(
                    {'source': host, 'quality': quality, 'language': 'de', 
                     'url': link, 'info': info, 'direct': False, 
                     'priority': self.priority, 'prioHoster': prioHoster})
            return self.sources
        except:
            return self.sources

    def resolve(self, url):
        try:
            return url
        except:
            return
