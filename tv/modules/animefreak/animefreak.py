import mc, re, os, sys
sys.path.append(os.path.join(mc.GetApp().GetAppDir(), 'libs'))
import ba
from urllib import quote_plus
from urllib2 import *
import csv
from beautifulsoup.BeautifulSoup import BeautifulSoup

class Module(object):
    def __init__(self):
        self.name = "Anime Freak TV"               #Name of the channel
        self.type = ['list']              #Choose between 'search', 'list', 'genre'
        self.episode = True                         #True if the list has episodes
        self.filter = []                            #Option to set a filter to the list
        self.genre = []                             #Array to add a genres to the genre section [type genre must be enabled]
        self.content_type = ''                  #Mime type of the content to be played
        self.country = ''                         #2 character country id code

        
        self.url_base = 'http://www.animefreak.tv'
        self.exclude = []

    def List(self):
        url = self.url_base + '/book'
        data = ba.FetchUrl(url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        div_main  = soup.findAll( 'div', {'id' : 'primary'})[0]
        div_show  = div_main.findAll( 'div', {'class' : 'item-list'})[0]

        streamlist = list()
        for info in div_show.findAll('a'):
            stream = ba.CreateStream()
            name = info.contents[0]
            id = self.url_base + info['href']
            if not name in self.exclude:
                stream.SetName(name)
                stream.SetId(id)
                streamlist.append(stream)

        return streamlist

    def Episode(self, stream_name, stream_id, page, totalpage):
        data = ba.FetchUrl(stream_id, 3600)

        if data == "":
            mc.ShowDialogNotification("Geen afleveringen gevonden voor " + str(stream_name))
            return [ba.CreateEpisode()]

        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")

        if totalpage == "":
            totalpage = 1

        div_content = soup.findAll('div', {'class' : 'content'})[0]
        thumb = div_content.findAll('img', {'align' : 'left'})[0]
        div_main = soup.findAll('div', {'class' : 'book-navigation'})[0]

        episodelist = list()
        for info in div_main.findAll('a'):
            episode = ba.CreateEpisode()
            episode.SetName(info.contents[0].split('Episode')[0])
            episode.SetId(self.url_base + info['href'])
            episode.SetThumbnails(thumb['src'])
            episode.SetDate('Episode' + info.contents[0].split('Episode')[1])
            episode.SetPage(page)
            episode.SetTotalpage(totalpage)
            episodelist.append(episode)

        return episodelist

    def Play(self, stream_name, stream_id, subtitle):
        url = stream_id +'|http://navix.turner3d.net/proc/animefreak'
        path = self.GetPath(url)

        play = ba.CreatePlay()
        if 'youtube.com' in path:
            play.SetPath(path)
            play.SetDomain('youtube.com')
            play.SetJSactions('')
            play.SetContent_type('video/x-flv')
        elif 'http' in path:
            play.SetPath(path)
        elif 'mms' in path:
            play.SetPath(path)
        elif 'rtmp' in path:
            play.SetPath(path)
        else:
            mc.ShowDialogNotification("Data format currently not supported")
            play.SetPath('')
        return play

    ####From navi-x module
    #########################
    def ParseProcessor(self, url):
        data = csv.reader(urlopen(url), delimiter="'", quoting=csv.QUOTE_NONE, quotechar='|')

        datalist = {}
        keys = []
        for i, line in enumerate(data):
            if line:
                if len(line) == 1:
                    datalist[i] = line[0]
                if len(line) == 2:
                    if line[0] not in keys:
                        datalist[line[0]] = line[1]
                        keys.append(line[0])
        return datalist

    def GetPath(self, stream_id):
        if len(stream_id.split('|')) > 1:
            urlpart = stream_id.split('|')
            url = urlpart[1] + '?url=' + urlpart[0]
            data = self.ParseProcessor(url)
            keys = data.keys()

            if len(data) < 2:
                return

            try:
                if data[0] == 'v2':
                    id = 1
            except:
                """"""

            try:
                if 'http' in data[0]:
                    id = 2
            except:
                """"""

            if id == 1:
                id_url = ''
                id_cookie = ''
                id_regex = ''
                id_postdata = ''

                if 's_url=' in keys: id_url = data['s_url=']
                if 's_cookie=' in keys: id_cookie = data['s_cookie=']
                if 'regex=' in keys: id_regex = data['regex=']
                if 's_postdata=' in keys: id_postdata = data['s_postdata=']
                if not id_url: id_url = urlpart[0]

                data = ba.FetchUrl(str(id_url), 0, False, str(id_postdata), str(id_cookie))

                try:
                    path = re.compile(str(id_regex), re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
                except:
                    path = ""


            elif id == 2:
                id_url = data[0]
                id_regex = data[1]
                data = ba.FetchUrl(str(id_url))
                if 'megavideo' in id_url:
                    try:
                        k1, k2, un, s = re.search(str(id_regex), str(data)).groups()
                        path = "http://www" + s + ".megavideo.com/files/" + self.decrypt(un, k1, k2) + "/"
                    except:
                        path = ""
                else:
                    try:
                        path = re.compile(str(id_regex), re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
                    except:
                        path = ""

            else:
                path = ""
        else:
            path = stream_id

        return path

    ########## Megavideo Addition
    def decrypt(self, str1, key1, key2):

        __reg1 = []
        __reg3 = 0
        while (__reg3 < len(str1)):
            __reg0 = str1[__reg3]
            holder = __reg0
            if (holder == "0"):
                __reg1.append("0000")
            else:
                if (__reg0 == "1"):
                    __reg1.append("0001")
                else:
                    if (__reg0 == "2"):
                        __reg1.append("0010")
                    else:
                        if (__reg0 == "3"):
                            __reg1.append("0011")
                        else:
                            if (__reg0 == "4"):
                                __reg1.append("0100")
                            else:
                                if (__reg0 == "5"):
                                    __reg1.append("0101")
                                else:
                                    if (__reg0 == "6"):
                                        __reg1.append("0110")
                                    else:
                                        if (__reg0 == "7"):
                                            __reg1.append("0111")
                                        else:
                                            if (__reg0 == "8"):
                                                __reg1.append("1000")
                                            else:
                                                if (__reg0 == "9"):
                                                    __reg1.append("1001")
                                                else:
                                                    if (__reg0 == "a"):
                                                        __reg1.append("1010")
                                                    else:
                                                        if (__reg0 == "b"):
                                                            __reg1.append("1011")
                                                        else:
                                                            if (__reg0 == "c"):
                                                                __reg1.append("1100")
                                                            else:
                                                                if (__reg0 == "d"):
                                                                    __reg1.append("1101")
                                                                else:
                                                                    if (__reg0 == "e"):
                                                                        __reg1.append("1110")
                                                                    else:
                                                                        if (__reg0 == "f"):
                                                                            __reg1.append("1111")

            __reg3 = __reg3 + 1

        mtstr = ajoin(__reg1)
        __reg1 = asplit(mtstr)
        __reg6 = []
        __reg3 = 0
        while (__reg3 < 384):

            key1 = (int(key1) * 11 + 77213) % 81371
            key2 = (int(key2) * 17 + 92717) % 192811
            __reg6.append((int(key1) + int(key2)) % 128)
            __reg3 = __reg3 + 1

        __reg3 = 256
        while (__reg3 >= 0):

            __reg5 = __reg6[__reg3]
            __reg4 = __reg3 % 128
            __reg8 = __reg1[__reg5]
            __reg1[__reg5] = __reg1[__reg4]
            __reg1[__reg4] = __reg8
            __reg3 = __reg3 - 1

        __reg3 = 0
        while (__reg3 < 128):

            __reg1[__reg3] = int(__reg1[__reg3]) ^ int(__reg6[__reg3 + 256]) & 1
            __reg3 = __reg3 + 1

        __reg12 = ajoin(__reg1)
        __reg7 = []
        __reg3 = 0
        while (__reg3 < len(__reg12)):

            __reg9 = __reg12[__reg3:__reg3 + 4]
            __reg7.append(__reg9)
            __reg3 = __reg3 + 4


        __reg2 = []
        __reg3 = 0
        while (__reg3 < len(__reg7)):
            __reg0 = __reg7[__reg3]
            holder2 = __reg0

            if (holder2 == "0000"):
                __reg2.append("0")
            else:
                if (__reg0 == "0001"):
                    __reg2.append("1")
                else:
                    if (__reg0 == "0010"):
                        __reg2.append("2")
                    else:
                        if (__reg0 == "0011"):
                            __reg2.append("3")
                        else:
                            if (__reg0 == "0100"):
                                __reg2.append("4")
                            else:
                                if (__reg0 == "0101"):
                                    __reg2.append("5")
                                else:
                                    if (__reg0 == "0110"):
                                        __reg2.append("6")
                                    else:
                                        if (__reg0 == "0111"):
                                            __reg2.append("7")
                                        else:
                                            if (__reg0 == "1000"):
                                                __reg2.append("8")
                                            else:
                                                if (__reg0 == "1001"):
                                                    __reg2.append("9")
                                                else:
                                                    if (__reg0 == "1010"):
                                                        __reg2.append("a")
                                                    else:
                                                        if (__reg0 == "1011"):
                                                            __reg2.append("b")
                                                        else:
                                                            if (__reg0 == "1100"):
                                                                __reg2.append("c")
                                                            else:
                                                                if (__reg0 == "1101"):
                                                                    __reg2.append("d")
                                                                else:
                                                                    if (__reg0 == "1110"):
                                                                        __reg2.append("e")
                                                                    else:
                                                                        if (__reg0 == "1111"):
                                                                            __reg2.append("f")

            __reg3 = __reg3 + 1

        endstr = ajoin(__reg2)
        return endstr

def ajoin(arr):
    strtest = ''
    for num in range(len(arr)):
        strtest = strtest + str(arr[num])
    return strtest

def asplit(mystring):
    arr = []
    for num in range(len(mystring)):
        arr.append(mystring[num])
    return arr