import mc, re, os, sys
sys.path.append(os.path.join(mc.GetApp().GetAppDir(), 'libs'))
import ba
from beautifulsoup.BeautifulSoup import BeautifulSoup
from itertools import izip

class Module(object):
    def __init__(self):
        self.name = "China TV"                      #Name of the channel
        self.type = ['list']                        #Choose between 'search', 'list', 'genre'
        self.episode = False                        #True if the list has episodes
        self.filter = []                            #Option to set a filter to the list
        self.genre = []                             #Array to add a genres to the genre section [type genre must be enabled]
        self.content_type = 'video/x-ms-wmv'        #Mime type of the content to be played
        self.country = 'CN'                         #2 character country id code

        self.base_url = 'http://beelinetv.com/free_chinese_tv/'

    def List(self):
        data = ba.FetchUrl(self.base_url )
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")
        div = soup.findAll('div', {'id':'mainContent'})[0]

        title = []
        path = []

        for info in div.findAll('a', {'class' : 's'}):
            title_id = info.contents[0]
            title.append(title_id)

        for info in div.findAll('a', {'class' : 'b'}):
            path_id = info['href']
            path.append(path_id)

        streamlist = list()
        for title_i,path_i in izip(title,path):
            stream = ba.CreateStream()
            stream.SetName(title_i)
            stream.SetId(path_i)
            streamlist.append(stream)

        return streamlist

    def Play(self, stream_name, stream_id, subtitle):
        play = ba.CreatePlay()
        play.SetPath(stream_id)

        return play

   