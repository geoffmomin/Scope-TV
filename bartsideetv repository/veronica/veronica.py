from default import *
from library import *
import tools

sys.path.append(os.path.join(CWD, 'external'))

from BeautifulSoup import BeautifulSoup
from itertools import izip

class Module(BARTSIDEE_MODULE):
    def __init__(self, app):
        self.app            = app
        BARTSIDEE_MODULE.__init__(self, app)

        self.name           = "Veronica Gemist"              #Name of the channel
        self.type           = ['list']                       #Choose between 'search', 'list', 'genre'
        self.episode        = True                           #True if the list has episodes
        self.content_type   = 'video/x-ms-asf'               #Mime type of the content to be played
        self.country        = 'NL'                           #2 character country id code

        
        self.url_base       = 'http://www.veronicatv.nl'
        self.url_home       = '%s/web/show/id=997234/langid=43' % self.url_base
        self.exclude        = []

    def List(self):
        url  = self.url_home
        data = tools.urlopen(self.app, url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        div_main  = soup.findAll( 'div', {'class' : 'mo-a alphabetical'})[0]
        div_show  = div_main.findAll( 'div', {'class' : 'wrapper'})[0]

        streamlist = list()
        for info in div_show.findAll('a'):
            stream = CreateList()
            name   = info.contents[0]
            if info.has_key('href'):
                id     = self.url_base + info['href']
                if not name in self.exclude:
                    stream.name     = name
                    stream.id       = id
                    streamlist.append(stream)

        return streamlist

    def Episode(self, stream_name, stream_id, page, totalpage):
        url = str(stream_id) + '/page=' + str(page)
        data = tools.urlopen(self.app, url, {'cache':3600})

        if len(data) < 10:
            mc.ShowDialogNotification("Geen afleveringen gevonden voor " + str(stream_name))
            return []

        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        if totalpage == 1:
            try:
                pages = soup.findAll( 'div', {'class' : 'paginator'})[0]
                pages = pages.findAll('span')
                totalpage = len(pages) - 1
            except:
                totalpage = 1

        div_main = soup.findAll('div', {'class' : 'mo-c double'})[0]
        div_show = div_main.findAll('div', {'class' : 'wrapper'})[0]

        info    = div_show.findAll('div', {'class' : 'thumb'})
        airtime = div_show.findAll('div', {'class' : 'airtime'})

        if len(info) < 1:
            mc.ShowDialogNotification("Geen afleveringen gevonden voor " + str(stream_name))
            return []

        episodelist = list()
        for info_i, airtime_i in izip(info, airtime):
            episode             = CreateEpisode()
            episode.name        = stream_name
            episode.id          = self.url_base + info_i.a['href']
            episode.thumbnails  = self.url_base + info_i.find('img')['src']
            episode.date        = airtime_i.a.span.contents[0]
            episode.page        = page
            episode.totalpage   = totalpage
            episodelist.append(episode)

        return episodelist

    def Play(self, stream_name, stream_id, subtitle):
        data     = tools.urlopen(self.app, stream_id)
        url_play = re.compile('<a class="wmv-player-holder" href="(.*?)"></a>', re.DOTALL + re.IGNORECASE).search(data).group(1)

        play       = CreatePlay()
        play.path  = url_play

        return play
