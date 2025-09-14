# edit 2025-02-12

import re
import datetime
from resources.lib.control import getSetting, urljoin, setSetting
from resources.lib.requestHandler import cRequestHandler
from scrapers.modules import cleantitle, dom_parser
from resources.lib.utils import isBlockedHoster

SITE_IDENTIFIER = 'aniworld'
SITE_DOMAIN = 'aniworld.to'  # https://www.aniworld.info/
SITE_NAME = SITE_IDENTIFIER.upper()

date = datetime.date.today()
currentyear = int(date.strftime("%Y"))

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domain = getSetting('provider.' + SITE_IDENTIFIER + '.domain', SITE_DOMAIN)
        self.base_link = 'https://' + self.domain
        self.search_link = '/animes'
        self.sources = []

    def run(self, titles, year, season=0, episode=0, imdb='', hostDict=None):
        sources = []
        if season == 0: 
            return sources
        try:
            t = [cleantitle.get(i) for i in titles if i]
            url = urljoin(self.base_link, self.search_link)

            oRequest = cRequestHandler(url)
            oRequest.cacheTime = 60*60*24
            sHtmlContent = oRequest.request()

            links = dom_parser.parse_dom(sHtmlContent, "div", attrs={"class": "genre"})
            links = dom_parser.parse_dom(links, "a")
            links = [(i.attrs["href"], i.content) for i in links]

            url = ''
            aLinks = []
            for i in links:
                try:
                    if cleantitle.get(i[1]) in t:
                        url = i[0]
                        break
                except:
                    pass

            if url == '':
                for i in links:
                    for a in t:
                        try:
                            if any([a in cleantitle.get(i[1])]):
                                aLinks.append({'source': i[0]})
                                break
                        except:
                            pass

            if url == '':
                if len(aLinks) > 0:
                    for i in aLinks:
                        url = i['source']
                        self.run2(url, year, season=season, episode=episode, hostDict=hostDict, imdb=imdb)
                else:
                    return sources
            else:
                self.run2(url, year, season=season, episode=episode, hostDict=hostDict, imdb=imdb)
        except:
            return sources
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

            r = dom_parser.parse_dom(sHtmlContent, 'div', attrs={'class': 'hosterSiteVideo'})
            r = dom_parser.parse_dom(r, 'li', attrs={'data-lang-key': re.compile('[1|3]')})  # nur deutsch + subbed DE

            r = [(i.attrs['data-link-target'], dom_parser.parse_dom(i, 'h4'),
                  'Untertitel DE' if i.attrs['data-lang-key'] == '3' else '' if i.attrs['data-lang-key'] == '1' else 'Untertitel EN' if i.attrs['data-lang-key'] == '2' else '') for i in r]

            r = [(i[0], re.sub('\s(.*)', '', i[1][0].content), 'HD' if 'hd' in i[1][0][1].lower() else 'SD', i[2]) for i in r]

            for link, host, quality, info in r:
                quality = 'HD'  # temp
                isBlocked, hoster, url, prioHoster = isBlockedHoster(host, isResolve=False)
                if isBlocked: 
                    continue
                self.sources.append(
                    {'source': host, 'quality': quality, 'language': 'de', 'url': link, 'info': info,
                     'direct': False, 'priority': self.priority, 'prioHoster': prioHoster})
            return self.sources
        except:
            return self.sources

    def resolve(self, url):
        try:
            Request = cRequestHandler(self.base_link + url, caching=False)
            Request.addHeaderEntry('Referer', self.base_link)
            Request.addHeaderEntry('Upgrade-Insecure-Requests', '1')
            Request.request()
            return Request.getRealUrl()
        except:
            return
