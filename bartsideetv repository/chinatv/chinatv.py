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

        self.name           = "China TV"                        #Name of the channel
        self.type           = ['list']                          #Choose between 'search', 'list', 'genre'
        self.episode        = False                             #True if the list has episodes
        self.content_type   = 'video/x-ms-wmv'                  #Mime type of the content to be played
        self.country        = 'CN'                              #2 character country id code

        self.base_url       = 'http://beelinetv.com/free_chinese_tv/'

    def List(self):
        data = tools.urlopen(self.app, self.base_url )
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
            stream          =   CreateList()
            stream.name     =   title_i
            stream.id       =   path_i
            streamlist.append(stream)

        return streamlist

    def Play(self, stream_name, stream_id, subtitle):
        play        =   CreatePlay()
        play.path   =   stream_id

        return play

   