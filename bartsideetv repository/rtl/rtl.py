import mc, re, os, sys
sys.path.append(os.path.join(mc.GetApp().GetAppDir(), 'libs'))
import ba
import simplejson as json
import datetime, time

class Module(object):
    def __init__(self):
        self.name = "RTL Gemist"                    #Name of the channel
        self.type = ['list', 'genre']               #Choose between 'search', 'list', 'genre'
        self.episode = True                         #True if the list has episodes
        self.filter = []                            #Option to set a filter to the list
        self.genrelist = {}
        self.genre = []                             #Array to add a genres to the genre section [type genre must be enabled]
        self.content_type = 'video/mp4'             #Mime type of the content to be played
        self.country = 'NL'                         #2 character country id code

        self.initDate()

    def List(self):
        json = self.retreive()

        unique = []
        streamlist = list()
        for info in json:
            name = info['serie'].encode('utf-8')
            if not name in unique:
                stream = ba.CreateStream()
                stream.SetName(name)
                stream.SetId(name)
                streamlist.append(stream)
                unique.append(name)

        return streamlist

    def Episode(self, stream_name, stream_id, page, totalpage):
        json = self.retreive()

        episodes = self.select_sublist(json, serie=unicode(stream_id) )

        if len(episodes) == "":
            mc.ShowDialogNotification("Geen afleveringen gevonden voor " + str(stream_name))
            return ba.CreateEpisode()

        if totalpage == "":
            totalpage = 1

        episodelist = list()
        unique = []
        for info in episodes:
            date = info['time']
            if date not in unique:
                episode = ba.CreateEpisode()
                episode.SetName( info['serie'].encode('utf-8') )
                episode.SetId( str(info['path']) )
                episode.SetThumbnails( str(info['thumbnail']) )
                episode.SetDate( self.getDate(info['time'].split('T')[0]) )
                episode.SetDescription(info['description'].encode('utf-8'))
                episode.SetPage(page)
                episode.SetTotalpage(totalpage)
                episodelist.append(episode)
                unique.append(date)

        return episodelist

    def Genre(self, genre, filter, page, totalpage):
        json = self.retreive()

        date = self.genrelist[genre]
        episodes = self.select_sublist_regex(json, time=re.compile(date + ".*?"))

        genrelist = []
        if len(episodes) == "":
            mc.ShowDialogNotification("No genre found for " + str(genre))
            return genrelist

        if totalpage == "":
            totalpage = 1

        genrelist = list()
        unique = []
        for info in episodes:
            date = str(info['time'])
            if date not in unique:
                broadcast = date.split('T')
                genreitem = ba.CreateEpisode()
                genreitem.SetName( info['title'].encode('utf-8') )
                genreitem.SetId( str(info['path']) )
                genreitem.SetDescription( str( broadcast[0] ) + ' - ' + info['description'].encode('utf-8') )
                genreitem.SetThumbnails( str(info['thumbnail']) )
                genreitem.SetDate( str( broadcast[1][:5] ) )
                genreitem.SetPage( page )
                genreitem.SetTotalpage( totalpage )
                genrelist.append( genreitem )
                unique.append( date )

        return genrelist

    def Play(self, stream_name, stream_id, subtitle):
        play = ba.CreatePlay()
        play.SetPath(stream_id)

        return play

    def retreive(self, time=3600):
        url = "http://pipes.yahoo.com/pipes/pipe.run?_id=38ab6e536929bebf4fdb79d2cff82b8f&_render=json&_maxage="+str(time)
        if time ==3600:
            data = ba.FetchUrl(url, 5400)
        else:
            data = ba.FetchUrl(url, 0)
        data = json.loads(data)['value']['items']
        if len(data) < 3 and time == 3600:
            return self.retreive(10)
        return data

		

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