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

        self.name           = "Hulu"                            #Name of the channel
        self.type           = ['search', 'genre']               #Choose between 'search', 'list', 'genre'
        self.episode        = True                              #True if the list has episodes
        self.filterlist     = {'All TV':'tv', 'TV Clips':'clips', 'TV Episodes':'episodes','Games':'games' ,'All Movies':'movies' ,'Movie Clips':'film_clips' ,'Movie Trailers':'film_trailers' ,'Feature Films':'feature_films'}
        self.filter         = self.filterlist.keys()
        self.genre          = ['popular','recent']              #Array to add a genres to the genre section [type genre must be enabled]
        self.content_type   = 'video/x-flv'                     #Mime type of the content to be played
        self.country        = 'US'                              #2 character country id code
        
        self.url_base       = 'http://www.hulu.com'

    def Search(self, search):
        url  = self.url_base + '/browse/search?alphabet=All&family_friendly=0&closed_captioned=0&has_free=1&has_huluplus=0&has_hd=0&channel=All&subchannel=&network=All&display=Shows%20with%20full%20episodes%20only&decade=All&type=tv&view_as_thumbnail=false&block_num=0&keyword=' + quote_plus(search)
        data = tools.urlopen(self.app, url)

        data = re.compile('"show_list", "(.*?)"\)', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
        data = data.replace('\\u003c','<').replace('\\u003e','>').replace('\\','').replace('\\n','').replace('\\t','')
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        streamlist = list()
        for info in soup.findAll('a', {'onclick':True}):
            stream         = CreateList()
            stream.name    = info.contents[0]
            stream.id      = info['href']
            streamlist.append(stream)

        return streamlist
    
    def Episode(self, stream_name, stream_id, page, totalpage):
        data = tools.urlopen(self.app, stream_id, {'cache':3600})

        if not data:
            return []

        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")
        totalpage = len(soup.findAll('tr', 'srh'))

        try:
            episode_url = re.compile('VideoExpander.subheadingClicked\((.*?)\)"', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
        except:
            return []

        season_number = re.compile('season_number=(.*?)\&', re.DOTALL + re.IGNORECASE).search(str(episode_url)).group(1)
        show_id       = re.compile('show_id=(.*?)\&', re.DOTALL + re.IGNORECASE).search(str(episode_url)).group(1)

        pp = []
        for i in range(0,totalpage):
            pp.append(str(int(season_number) - i))
        intpage = int(page) - 1

        url  = self.url_base + "/videos/season_expander?order=desc&page=1&season_number=" + str(pp[intpage]) + "&show_id=" + str(show_id) + "&sort=season&video_type=episode"

        data = tools.urlopen(self.app, url)
        data = re.compile('srh-bottom-' + pp[intpage] +'", "(.*?)"\);', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
        data = data.replace('\\u003c','<').replace('\\u003e','>').replace('\\','')

        soup = BeautifulSoup(data)

        episodelist = list()
        name = []
        link = []
        number = []
        thumb = []
        for tmp in soup.findAll('td', {'class':'c0'}):
            number.append(tmp.contents[0])

        i = 0
        b = 0
        for tmp in soup.findAll('td', {'class':'c1'}):
            name.append(tmp.a.contents[0])
            link.append(tmp.a['href'])
            try:
                thumb.append(self.GetThumb(re.compile('/watch/(.*?)/', re.DOTALL + re.IGNORECASE).search(str(tmp.a['href'])).group(1)))
            except:
                thumb.append('')
            b += 1
            if len(tmp.findAll('div', 'vex-h')) == 0:
                i += 1

        if not i: totalpage = page

        for x in xrange(0,b):
            if not 'plus' in link[x]:
                episode             =   CreateEpisode()
                episode.name        =   stream_name
                episode.id          =   link[x]
                episode.description =   'Episode: ' + str(number[x]) + ' - '  + str(name[x])
                episode.thumbnails  =   thumb[x]
                episode.date        =   'Season: ' + pp[intpage]
                episode.page        =   page
                episode.totalpage   =   totalpage
                episodelist.append(episode)

        return episodelist

    def Genre(self, genre, filter, page, totalpage):
        url = self.url_base + '/'+genre
        
        if filter != "":
            url = url + '/' + str(self.filterlist[filter])
        url  = url + '?'
        url  = url + 'page=' + str(page) +'&has_free=1'
        data = tools.urlopen(self.app, url, {'cache':3600})

        if data == "":
            mc.ShowDialogNotification("No genre found for " + str(genre))
            return []

        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")
        if totalpage == 1:
            totalpage = 10

        div_show = soup.find( 'table', {'id' : 'results_list'})

        genrelist = list()
        for info in div_show.findAll( 'div', {'class' : 'home-thumb'}):
            try:
                info.findAll(attrs={"class" : "clips_collection_background"})[0]
                episode = False
            except:
                episode = True

            if episode:
                div_title = info.findAll(attrs={"class" : "show-title-container"})[0]
                div_info = info.findAll(attrs={"class" : "video-info"})[0]

                path = div_title.a['href']
                title = div_title.a.contents[0]
                try:
                    desc = div_info.contents[0].replace('&nbsp;','')
                except:
                    desc = ''

                genreitem           =   CreateEpisode()
                genreitem.name      =   '[UPPERCASE]'+title +'[/UPPERCASE] ' + desc
                genreitem.id        =   path
                genreitem.page      =   page
                genreitem.totalpage =   totalpage
                genrelist.append(genreitem)

        return genrelist

    def Play(self, stream_name, stream_id, subtitle):
        path            =   self.tinyurl(stream_id)
        play            =   CreatePlay()
        play.path       =   quote_plus(path)
        play.domain     =   'bartsidee.nl'
        play.jsactions  =   quote_plus('http://bartsidee.nl/boxee/apps/js/hulu.js')
        return play

    def tinyurl(self, params):
        url = "http://tinyurl.com/api-create.php?url=" + str(params)
        return tools.urlopen(self.app, url)

    def GetThumb(self, id):
        url = "http://www.hulu.com/videos/info/" + str(id)
        data = tools.urlopen(self.app, url,{'xhr':True})
        try:
            return re.compile('"thumbnail_url":"(.*?)"', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
        except:
            try:
                return re.compile('"thumbnail_url": "(.*?)"', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
            except:
                return str('')