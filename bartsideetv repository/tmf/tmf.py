from default import *
from library import *
import tools

sys.path.append(os.path.join(CWD, 'external'))

from BeautifulSoup import BeautifulSoup
from urllib import quote, quote_plus

class Module(BARTSIDEE_MODULE):
    def __init__(self, app):
        self.app            = app
        BARTSIDEE_MODULE.__init__(self, app)

        self.name           = "TMF Music"                               #Name of the channel
        self.type           = ['search', 'genre']                       #Choose between 'search', 'list', 'genre'
        self.episode        = False                                     #True if the list has episodes
        self.genrelist      = {'Nieuw':'Z2VucmU9bmlldXcmbT12aWRlby9nZW5yZVRhYnM=', 'Pop':'Z2VucmU9cG9wJm09dmlkZW8vZ2VucmVUYWJz', 'Rock':'Z2VucmU9cm9jayAvIGFsdGVybmF0aXZlJm09dmlkZW8vZ2VucmVUYWJz', 'Dance':'Z2VucmU9ZGFuY2UmbT12aWRlby9nZW5yZVRhYnM=', 'Urban':'Z2VucmU9dXJiYW4mbT12aWRlby9nZW5yZVRhYnM=', 'Nl':'Z2VucmU9bmwmbT12aWRlby9nZW5yZVRhYnM='}
        self.genre          = self.genrelist.keys()                     #Array to add a genres to the genre section [type genre must be enabled]
        self.content_type   = 'video/x-flv'                             #Mime type of the content to be played
        self.country        = 'NL'                                      #2 character country id code

        self.url_base       = 'http://www.tmf.nl'

    def Search(self, search):
        url         = self.url_base + '/script/common/ajax_zoek.php'
        params      = 'keyword='+ quote(search)
        data        = tools.urlopen(self.app, url, {'post':params})

        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")

        streamlist = list()
        for info in soup.findAll('li'):
            title = re.compile('---(.*?)$', re.DOTALL + re.IGNORECASE).search(str(info.span.contents[0])[4:]).group(1)
            id    = re.compile('---(.*?)---', re.DOTALL + re.IGNORECASE).search(str(info.span.contents[0])).group(1)
            stream          = CreateList()
            stream.name     = title
            stream.id       = id
            streamlist.append(stream)
        return streamlist

    def Genre(self, genre, filter, page, totalpage):
        url  = 'http://www.tmf.nl/ajax/?genreTabs=' + self.genrelist[genre]
        data = tools.urlopen(self.app, url, {'cache':3600, 'xhr':True})
        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")

        genrelist = list()
        if len(data) < 1:
            mc.ShowDialogNotification("No data found for " + str(genre))
            return []

        for info in soup.findAll('div',{'class':'title'}):
            link = info.a['href']
            id = re.compile('video\/(.*?)\/', re.DOTALL + re.IGNORECASE).search(link).group(1)
            genreitem           = CreateEpisode()
            genreitem.name      = info.a['title']
            genreitem.id        = id
            genreitem.page      = page
            genreitem.totalpage = totalpage
            genrelist.append(genreitem)

        if len(genrelist) < 1 :
            mc.ShowDialogNotification("No data found for " + str(genre))

        return genrelist

    def Play(self, stream_name, stream_id, subtitle):
        url             = 'http://www.tmf.nl/video/'+stream_id
        play            = CreatePlay()
        play.path       = quote_plus(url)
        play.domain     = 'tmf.nl'
        play.jsactions  = quote_plus('http://boxee.bartsidee.nl/apps/js/tmf.js')
        return play
