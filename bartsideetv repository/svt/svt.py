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

        self.name           = "Svt play"                            #Name of the channel
        self.type           = ['list']                              #Choose between 'search', 'list', 'genre'
        self.episode        = True                                  #True if the list has episodes
        self.content_type   = 'video/x-flv'                         #Mime type of the content to be played
        self.country        = 'SE'                                  #2 character country id code

        self.url_base       = 'http://svtplay.se'

    def List(self):
        url = self.url_base + '/alfabetisk'
        data = tools.urlopen(self.app, url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        div_main  = soup.findAll( 'div', {'class' : 'tab active'})[0]

        streamlist = list()
        for info in div_main.findAll('a'):
            if len(info.contents[0]) > 4:
                stream          = CreateList()
                stream.name     = info.contents[0]
                stream.id       = info['href']
                streamlist.append(stream)

        return streamlist

    def Episode(self, stream_name, stream_id, page, totalpage):
        url = self.url_base + stream_id + '?ajax,sb/sb'
        data = tools.urlopen(self.app, url, {'cache':3600})

        if data == "":
            mc.ShowDialogNotification("No episode found for " + str(stream_name))
            return []

        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")

        episodelist = list()
        for info in soup.findAll('li'):
            if len(info.a.findAll('em')) > 0:
                episode                 =   CreateEpisode()
                episode.name            =   stream_name
                episode.id              =   info.a['href']
                episode.description     =   info.a.span.contents[0].replace(' ','').replace('\n','').replace('\t','')
                episode.thumbnails      =   info.a.img['src']
                episode.date            =   info.a.em.contents[0][-10:]
                episode.page            =   page
                episode.totalpage       =   totalpage
                episodelist.append(episode)

        return episodelist

    def Play(self, stream_name, stream_id, subtitle):
        url     = self.url_base + stream_id
        data    = tools.urlopen(self.app, url)
        play    = CreatePlay()
	try:
            data    = re.compile('dynamicStreams=url:(.*?)\.mp4', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
            domain  = re.compile('^(.*?)/kluster', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
            id      = re.compile('_definst_/(.*?)$', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
        except:
            mc.ShowDialogNotification("No stream found for " + str(stream_name))
            return play
		
	url             = 'http://www.bartsidee.nl/flowplayer/index.html?net=' + str(domain) + '&id=mp4:' + str(id) + '.mp4'
        play.path       = quote_plus(url)
        play.domain     = 'bartsidee.nl'
        play.jsactions  = quote_plus('http://bartsidee.nl/boxee/apps/js/flow.js')

        return play
