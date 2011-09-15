from default import *
from library import *
import tools

sys.path.append(os.path.join(CWD, 'external'))

from BeautifulSoup import BeautifulSoup
from urllib import quote_plus, quote
import simplejson as json

class Module(BARTSIDEE_MODULE):
    def __init__(self, app):
        self.app            = app
        BARTSIDEE_MODULE.__init__(self, app)

        self.name           = "BBC iPlayer"                #Name of the channel
        self.type           = ['search', 'genre']          #Choose between 'search', 'list', 'genre'
        self.episode        = True                         #True if the list has episodes
        self.genre          = []                           #Array to add a genres to the genre section [type genre must be enabled]
        self.content_type   = 'video/x-flv'                #Mime type of the content to be played
        self.country        = 'UK'                         #2 character country id code
        
        self.url_base = 'http://www.bbc.co.uk'
        #self.genre_links = {"Children's":"childrens", "Comedy":"comedy", "Drama":"drama", "Entertainment":"entertainment", "Factual":"factual", "Films":"films", "Learning":"learning", "Lifestyle and Leisure":"lifestyle_and_leisure", "Music":"music", "News":"news", "Religion and Ethics":"religion_and_ethics", "Sport":"sport", "Northern Ireland":"northern_ireland", "Scotland":"scotland", "Wales":"wales", "Audio Described":"audiodescribed", "Sign Zone":"signed"}
        self.genre_links = {"Children's":"9100001", "Comedy":"9100098", "Drama":"9100003", "Entertainment":"9100099", "Factual":"9100005", "Films":"9100093", "Learning":"9100004", "Lifestyle and Leisure":"9300054", "Music":"9100006", "News":"9100007", "Religion and Ethics":"9100008", "Sport":"9100010", "Northern Ireland":"9100094", "Scotland":"9100095", "Wales":"9100097", "Audio Described":"dubbedaudiodescribed", "Sign Zone":"signed"}
        self.Categories()

    def Search(self, search):
        url     = 'http://search.bbc.co.uk/suggest?scope=iplayer&format=xml&callback=xml.suggest&q=' + quote_plus(search)
        data    = tools.urlopen(self.app, url)

        soup    = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")

        streamlist = list()
        for info in soup.findAll('text'):
            stream      =   CreateList()
            stream.name =   info.contents[0]
            stream.id   =   ConvertASCII(info.contents[0])
            streamlist.append(stream)

        return streamlist
    
    def Episode(self, stream_name, stream_id, page, totalpage):
        url = self.url_base + '/iplayer/widget/startswith/site/bigscreen/media_set/pc-bigscreen/json/1/bigscreen_layout/sd/service_type/tv/template/index/starts_with/' + quote(stream_id)
        data = tools.urlopen(self.app, url, {'cache':3600})

        if len(data) < 10:
            mc.ShowDialogNotification("No episode found for " + str(stream_name))
            episodelist = list()
            return episodelist

        json_data = json.loads(data)

        episodelist = list()
        for info in json_data['data']:
            episode             =   CreateEpisode()
            episode.name        =   info['s']
            episode.id          =   self.url_base + info['url']
            episode.thumbnails  =   'http://node1.bbcimg.co.uk/iplayer/images/episode/' + re.compile('episode\/(.*?)\/', re.DOTALL + re.IGNORECASE).search(info['url']).group(1) + '_288_162.jpg'
            episode.date        =   info['t']
            episode.page        =   page
            episode.totalpage   =   totalpage
            episodelist.append(episode)
        return episodelist

    def Genre(self, genre, filter, page, totalpage):
        url = self.url_base + '/iplayer/widget/listview/site/bigscreen/media_set/pc-bigscreen/json/1/bigscreen_layout/sd/service_type/tv/category/' + quote(self.genre_links[genre]) + '/perpage/100/block_type/episode'
        data = tools.urlopen(self.app, url, {'cache':3600})

        if len(data) < 10:
            mc.ShowDialogNotification("No episode found for " + str(stream_name))
            episodelist = list()
            return episodelist

        json_data = json.loads(data)
        
        genrelist = list()
        for info in json_data['data']:
            genreitem           =   CreateEpisode()
            genreitem.name      =   info['s']
            genreitem.id        =   self.url_base + info['url']
            genreitem.date      =   info['t']
            genreitem.page      =   page
            genreitem.totalpage =   totalpage
            genrelist.append(genreitem)

        return genrelist

    def Play(self, stream_name, stream_id, subtitle):

        id = re.compile('episode\/(.*?)\/', re.DOTALL + re.IGNORECASE).search(str(stream_id)).group(1)
        url = self.url_base + '/iplayer/episode/' + id + '/'
 
        if subtitle:
            play            =   CreatePlay()
            play.path       =   quote_plus(url)
            play.domain     =   'bbc.co.uk'
            play.jsctions   =   quote_plus('http://bartsidee.nl/boxee/apps/js/bbc1.js')
        else:
            play            =   CreatePlay()
            play.path       =   quote_plus(url)
            play.domain     =   'bbc.co.uk'
            play.jsactions  =   quote_plus('http://bartsidee.nl/boxee/apps/js/bbc0.js')

        return play

    def Categories(self):
        for key in self.genre_links.keys():
            self.genre.append(key)