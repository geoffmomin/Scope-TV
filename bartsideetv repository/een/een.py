from default import *
from library import *
import tools

sys.path.append(os.path.join(CWD, 'external'))

from BeautifulSoup import BeautifulSoup
from urllib import quote_plus

class Module(BARTSIDEE_MODULE):
    def __init__(self, app):
        self.app            = app
        BARTSIDEE_MODULE.__init__(self, app)

        self.name           = "Een"                             #Name of the channel
        self.type           = ['list']                          #Choose between 'search', 'list', 'genre'
        self.episode        = True                              #True if the list has episodes
        self.content_type   = 'video/x-flv'                     #Mime type of the content to be played
        self.country        = 'BE'                              #2 character country id code


        self.url_base       = 'http://www.een.be/mediatheek'

    def List(self):
        url = self.url_base
        data = tools.urlopen(self.app, url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        div_main = soup.findAll('select', {'name':'programmas'})[0]

        streamlist = []
        items = div_main.findAll('option')
        items.pop(0)
        for item in items:

            stream = CreateList()
            stream.name     =   item.contents[0]
            stream.id       =   item['value']
            streamlist.append(stream)

        return streamlist

    def Episode(self, stream_name, stream_id, page, totalpage):
        url  = self.url_base + '/tag/' + str(stream_id) + '?page=' + str(page)
        data = tools.urlopen(self.app, url, {'cache':3600})
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        div_main = soup.findAll('div', {'class':'videoContainer'})[0]
        
        try:
            div_nav   = soup.findAll('span', {'class':'pager-list'} )[0]
            pages     = div_nav.findAll(attrs={'class' : re.compile("^pager-next")})
            totalpage = len(pages) +1
        except:
            totalpage = 1

        episodelist = list()
        for info in div_main.findAll('li'):
            episode                 =   CreateEpisode()
            episode.name            =   info.h5.a.contents[0]
            episode.id              =   info.a['href']
            episode.thumbnails      =   info.a.img['src']
            episode.page            =   page
            episode.totalpage       =   totalpage
            episodelist.append(episode)

        return episodelist

    def Play(self, stream_name, stream_id, subtitle):
        url  = 'http://www.een.be/mediatheek/ajax/video/' + str(stream_id).replace('/mediatheek/', '')
        data = tools.urlopen(self.app, url)

        file   = re.compile("file\: '(.*?)'").search(data).group(1)
        try:    domain = re.compile("streamer\: '(.*?)'").search(data).group(1)
        except: domain = False

        if domain:
            url                 =   'http://www.bartsidee.nl/flowplayer/index.html?net=' + str(domain) + '&id=' + str(file).replace('.flv', '')
            play                =   CreatePlay()
            play.content_type   =   'video/x-flv'
            play.path           =   quote_plus(url)
            play.domain         =   'bartsidee.nl'
            play.jsactions      =   quote_plus('http://bartsidee.nl/boxee/apps/js/flow.js')

        else:
            play                =   CreatePlay()
            play.path           =   file

        return play