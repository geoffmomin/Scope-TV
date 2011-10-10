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

        self.name           = "Canvas"                          #Name of the channel
        self.type           = ['list']                          #Choose between 'search', 'list', 'genre'
        self.episode        = True                              #True if the list has episodes
        self.content_type   = 'video/x-flv'                     #Mime type of the content to be played
        self.country        = 'BE'                              #2 character country id code


        self.url_base       = 'http://video.canvas.be/'

    def List(self):
        url = self.url_base
        data = tools.urlopen(self.app, url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        div_main = soup.find('div', {'id':'programma_menu'})

        streamlist = []
        for item in div_main.findAll('a'):
            stream = CreateList()
            stream.name     =   item.contents[0]
            stream.id       =   item['href']
            streamlist.append(stream)

        return streamlist

    def Episode(self, stream_name, stream_id, page, totalpage):
        url  = str(stream_id) + '/page/' + str(page)
        data = tools.urlopen(self.app, url, {'cache':3600})
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        div_main = soup.findAll('div', {'id':'videogallery'})[0]
        
        try:
            div_nav   = soup.findAll('div', {'class':'wp-pagenavi'} )[0]
            pages     = div_nav.findAll(attrs={'class' : re.compile("^page")})
            totalpage = len(pages) +1
        except:
            totalpage = 1

        episodelist = list()
        for info in div_main.findAll('div', {'class':'videoitem'}):
            div1  = info.findAll('div', {'class':'thumbnail'})[0]
            thumb = re.compile('background-image\: url\((.*?)\)').search(div1.div['style']).group(1)

            episode                 =   CreateEpisode()
            episode.name            =   div1.a['title']
            episode.id              =   div1.a['href']
            episode.description     =   ' '.join(info.p.a.contents[0].split())
            episode.thumbnails      =   thumb
            episode.page            =   page
            episode.totalpage       =   totalpage
            episodelist.append(episode)

        return episodelist

    def Play(self, stream_name, stream_id, subtitle):
        url  = str(stream_id)
        data = tools.urlopen(self.app, url, {'cache':3600})

        file   = re.compile('file \: "(.*?)"').search(data).group(1)
        try:    domain = re.compile('streamer \: "(.*?)"').search(data).group(1)
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