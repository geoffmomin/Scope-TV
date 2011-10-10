from default import *
from library import *
import tools

sys.path.append(os.path.join(CWD, 'external'))

from BeautifulSoup import BeautifulSoup
from itertools import izip
import datetime

class Module(BARTSIDEE_MODULE):
    def __init__(self, app):
        self.app            = app
        BARTSIDEE_MODULE.__init__(self, app)

        self.name           = "ZDF Mediathek"                   #Name of the channel
        self.type           = ['list', 'genre']                 #Choose between 'search', 'list', 'genre'
        self.episode        = True                              #True if the list has episodes
        self.content_type   = 'video/x-ms-asx'                  #Mime type of the content to be played
        self.country        = 'DE'                              #2 character country id code
        self.genre          = {}
        
        self.url_base       = 'http://www.zdf.de'
        self.initDate()

    def List(self):
        array = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        title = []
        id    = []
        for letter in array:
            url  = self.url_base + '/ZDFmediathek/xmlservice/web/sendungenAbisZ?characterRangeStart='+letter+'&detailLevel=2&characterRangeEnd='+letter
            data = tools.urlopen(self.app, url)
            soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")

            title.extend(soup.findAll('title'))
            id.extend(soup.findAll('assetid'))

        unique = dict([(key.contents[0], value.contents[0].replace('"','')) for key, value in izip(id, title)])
        order  = sorted(unique.items(), key=lambda x: x[1])
        
        streamlist = list()
        for (id, title) in order:
            stream          = CreateList()
            stream.name     = title
            stream.id       = id
            streamlist.append(stream)

        return streamlist
    
    def Episode(self, stream_name, stream_id, page, totalpage):

        url  = self.url_base + '/ZDFmediathek/xmlservice/web/aktuellste?id='+stream_id+'&maxLength=50'
        data = tools.urlopen(self.app, url, {'cache':3600})
        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")
        
        if len(data) < 5:
            mc.ShowDialogNotification("No episode found for " + str(stream_name))
            return []

        teaser = soup.findAll('teaser')

        episodelist = list()
        for info in teaser:
            if info.type.contents[0] == 'video':
                title   = info.find('title')
                title   = info.find('title')
                detail  = info.find('detail')
                id      = info.find('assetid')
                airtime = info.find('airtime')
                airtime = airtime.contents[0]
                thumb   = self.url_base + '/ZDFmediathek/contentblob/'+ str(id.contents[0]) +'/timg276x155blob'

                episode                 = CreateEpisode()
                episode.name            = title.contents[0]
                episode.id              = id.contents[0]
                episode.description     = stream_name + ': ' + encodeUTF8(detail.contents[0])
                episode.thumbnails      = thumb
                episode.date            = airtime
                episode.page            = page
                episode.totalpage       = totalpage
                episodelist.append(episode)

        return episodelist

    def Genre(self, genre, filter, page, totalpage):
        id   = self.genre[genre]
        url  = self.url_base + '/ZDFmediathek/xmlservice/web/sendungVerpasst?startdate=' + id +'&enddate='+id+'&maxLength=50'
        
        data = tools.urlopen(self.app, url, {'cache':2400})
        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")

        genrelist = list()
        if len(data) < 20:
            mc.ShowDialogNotification("No episode found for " + str(genre))
            return []

        teaser = soup.findAll('teaser')

        for info in teaser:
            if info.type.contents[0] == 'video':
                title   = info.find('title')
                id      = info.find('assetid')
                airtime = info.find('airtime')
                airtime = airtime.contents[0]

                genreitem               = CreateEpisode()
                genreitem.name          = title.contents[0]
                genreitem.id            = id.contents[0]
                genreitem.date          = airtime[-5:]
                genreitem.page          = page
                genreitem.totalpage     = totalpage
                genrelist.append(genreitem)

        if len(genrelist) < 1:
            mc.ShowDialogNotification("No episode found for " + str(genre))

        return genrelist
        
    def Play(self, stream_name, stream_id, subtitle):
        url  = 'http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?ak=web&id='+stream_id
        data = tools.urlopen(self.app, url)
        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")

        url  = soup.find('formitaet',{'basetype':'wmv3_wma9_asf_mms_asx_http'})
        url  = url.url.contents[0]

        sub  = soup.find('caption')
        try:
            sub = sub.url.contents[0]
        except:
            sub = ''

        play        = CreatePlay()
        play.path   = url
        if subtitle:
            if sub:
                play.subtitle           =   str(sub)
                play.setSubtitle_type   =   'flashxml'

        return play

    def initDate(self):
        now = datetime.datetime.now()
        for i in range(0, 6):
            newdate = now - datetime.timedelta(days=i)
            key = newdate.strftime("%d-%m-%y")
            if key == now.strftime("%d-%m-%y"):
                key = 'Heute'
            self.genre[key] = newdate.strftime("%d%m%y")


   