from default import *
from library import *
import tools

sys.path.append(os.path.join(CWD, 'external'))

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from urllib import quote_plus

class Module(BARTSIDEE_MODULE):
    def __init__(self, app):
        self.app            = app
        BARTSIDEE_MODULE.__init__(self, app)

        self.name           = "TV3 Play"                            #Name of the channel
        self.type           = ['list']                              #Choose between 'search', 'list', 'genre'
        self.episode        = True                                  #True if the list has episodes
        self.content_type   = 'video/x-flv'                         #Mime type of the content to be played
        self.country        = 'SE'                                  #2 character country id code

        self.url_base       = 'http://www.tv3play.se'

    def List(self):
        url = self.url_base + '/program'
        data = tools.urlopen(self.app, url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        div_main  = soup.findAll( 'div', {'id' : 'content'})[0]

        streamlist = list()
        for info in div_main.findAll('li'):
            if (info.prettify()) > 4:
                stream          = CreateList()
                stream.name     = info.a.contents[0]
                stream.id       = info.a['href']
                streamlist.append(stream)

        return streamlist

    def Episode(self, stream_name, stream_id, page, totalpage):
        url = self.url_base + stream_id

        data = tools.urlopen(self.app, url, {'cache':3600})

        if data == "":
            mc.ShowDialogNotification("No episode found for " + str(stream_name))
            return []

        rssfeed = re.compile('</a> <a href="(.*?)">RSS</a>').search(data).group(1)

        url = self.url_base + rssfeed
        data = tools.urlopen(self.app, url, {'cache':3600})
        soup = BeautifulStoneSoup(data, convertEntities="xml", smartQuotesTo="xml")

        episodelist = list()
        for info in soup.findAll('item'):
            episode                 =   CreateEpisode()
            episode.name            =   info.title.contents[0]
            episode.id              =   info.link.contents[0]
            episode.description     =   info.description.contents[0]
            episode.thumbnails      =   info.thumbnailimage.contents[0]
            episode.date            =   info.pubdate.contents[0]
            episode.page            =   page
            episode.totalpage       =   totalpage
            episodelist.append(episode)
        return episodelist

    def Play(self, stream_name, stream_id, subtitle):
        play    = CreatePlay()
        
        id    = re.compile('tv3play.se\/play\/(.*?)\/').search(str(stream_id)).group(1)

	url  = 'http://viastream.viasat.tv/PlayProduct/' + id
        data = tools.urlopen(self.app, url)
        soup = BeautifulStoneSoup(data, convertEntities="xml", smartQuotesTo="xml")
        
        video = soup.findAll('video')[0]
        video = '%r' % video.url.contents[0]
        video = video.replace("u'","").replace("'","")
        
        rtmp = video.split("/")
        rtmpURL  = "/".join(rtmp[:4])
        playPath = "/".join(rtmp[4:])
        authPath = ''

        play.rtmpurl        =   playPath
        play.rtmpdomain     =   rtmpURL
        play.rtmpauth       =   authPath

        return play
