from default import *
from library import *
import tools

sys.path.append(os.path.join(CWD, 'external'))

import simplejson as json
import datetime
import time

class Module(BARTSIDEE_MODULE):
    def __init__(self, app):
        self.app            = app
        BARTSIDEE_MODULE.__init__(self, app)

        self.name           = "RTL Gemist"                      #Name of the channel
        self.type           = ['list', 'genre']                 #Choose between 'search', 'list', 'genre'
        self.episode        = True                              #True if the list has episodes
        self.genrelist       = {}
        self.genre          = []                                #Array to add a genres to the genre section [type genre must be enabled]
        self.content_type   = 'video/mp4'                       #Mime type of the content to be played
        self.country        = 'NL'                              #2 character country id code

        self.initDate()

    def List(self):
        json = self.retreive()

        unique = []
        streamlist = list()
        for info in json:
            name = info['serienaam'].encode('utf-8')
            
            if not name in unique:
                stream              =   CreateList()
                stream.name         =   name
                stream.id           =   name
                streamlist.append(stream)
                unique.append(name)

        return streamlist

    def Episode(self, stream_name, stream_id, page, totalpage):
        json = self.retreive()

        episodes = self.select_sublist(json, serienaam=unicode(stream_id) )

        if len(episodes) == "":
            mc.ShowDialogNotification("Geen afleveringen gevonden voor " + str(stream_name))
            return []

        episodelist = list()
        unique = []
        for info in episodes:
            date = info['broadcastdatetime']
            if date not in unique:
                episode             =   CreateEpisode()
                episode.name        =   info['serienaam'].encode('utf-8')
                episode.id          =   str(info['movie'])
                episode.thumbnails  =   str(info['thumbnail'])
                episode.date        =   self.getDate(info['broadcastdatetime'].split('T')[0])
                episode.description =   info['samenvattingkort'].encode('utf-8')
                episode.page        =   page
                episode.totalpage   =   totalpage
                episodelist.append(episode)
                unique.append(date)

        return episodelist

    def Genre(self, genre, filter, page, totalpage):
        json = self.retreive()

        date = self.genrelist[genre]
        episodes = self.select_sublist_regex(json, broadcastdatetime=re.compile(date + ".*?"))

        if len(episodes) == "":
            mc.ShowDialogNotification("No genre found for " + str(genre))
            return []

        if totalpage == "":
            totalpage = 1

        genrelist = list()
        unique = []
        for info in episodes:
            date = str(info['broadcastdatetime'])
            if date not in unique:
                broadcast               =   date.split('T')
                genreitem               =   CreateEpisode()
                genreitem.name          =   info['title'].encode('utf-8')
                genreitem.id            =   str(info['movie'])
                genreitem.description   =   str( broadcast[0] ) + ' - ' + info['samenvattingkort'].encode('utf-8')
                genreitem.thumbnails    =   str(info['thumbnail'])
                genreitem.date          =   str( broadcast[1][:5] )
                genreitem.page          =   page
                genreitem.totalpage     =   totalpage
                genrelist.append( genreitem )
                unique.append( date )

        return genrelist

    def Play(self, stream_name, stream_id, subtitle):
        play        = CreatePlay()
        play.path   = stream_id

        return play

    def retreive(self, time=3600):
        url = "http://bartsidee.nl/boxee/tmp/rtl.json"
        if time ==3600:
            data = tools.urlopen(self.app, url, {'cache':5400})
        else:
            data = tools.urlopen(self.app, url)
        return json.loads(data)

		

    def select_sublist(self, list_of_dicts, **kwargs):
        return [dict(d) for d in list_of_dicts if all(d.get(k)==kwargs[k] for k in kwargs)]

    def select_sublist_regex(self, list_of_dicts, **kwargs):
        return [dict(d) for d in list_of_dicts if all(re.match(kwargs[k], d.get(k) ) for k in kwargs)]

    def initDate(self):
        now = datetime.datetime.now()
        for i in range(0, 6):
            newdate = now - datetime.timedelta(days=i)
            if i == 0:
                self.genrelist['Vandaag'] = newdate.strftime("%Y-%m-%d")
                self.genre.append('Vandaag')
            elif i == 1:
                self.genrelist['Gisteren'] = newdate.strftime("%Y-%m-%d")
                self.genre.append('Gisteren')
            else:
                self.genrelist[newdate.strftime("%d-%b")] = newdate.strftime("%Y-%m-%d")
                self.genre.append(newdate.strftime("%d-%b"))

    def getDate(self, datestring):
        c = time.strptime(datestring,"%Y-%m-%d")
        return time.strftime("%d-%b", c)

def all(iterable):
    for element in iterable:
        if not element:
            return False
    return True