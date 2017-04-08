import re
from pymystem3 import Mystem


class LinkQ:
    def __init__(self, rootlink):
        self.stops = [re.compile(stop) for stop in ['\.doc$', '\.avi$', 'javascript:', '\.txt$', '\s', '/rss',
                                                    '^[^h][a-z]+://']]
        self.links = [rootlink]

    def add_links(self, links):
        to_be = []
        for link in links:
            tb = True
            for stop in self.stops:
                if re.search(stop, link):
                    tb = False
                    break
            if tb:
                to_be.append(link.split('?')[0].split('#')[0])
        self.links += [link for link in set(to_be) if link not in self.links]


class Text:
    def __init__(self):
        self.stops = self.stopsget()
        self.mystem = Mystem(mystem_bin=None, grammar_info=False, disambiguation=False)
        self.stops_to_nil = [re.compile(st) for st in ['[0-9]+', '[.!?"\-,:—%*();»«]+']]

    def stopsget(self):
        with open('finstops.txt') as f:
            stops = [re.compile(u'(\s|^){}(\s)'.format(line.strip())) for line in f.readlines()]
        return stops

    def normalize(self, text):
        for stop_nil in self.stops_to_nil:
            text = re.sub(stop_nil, '', text)
        for stop in self.stops:
            text = re.sub(stop, '\\1\\2', text.lower())
        text = re.sub('  +', ' ', text)
        text = re.sub('\n ', '\n', text)
        tr = []
        for word in text.split():
            lemm = self.mystem.lemmatize(word)[0]
            tr.append(lemm)
        text = u' '.join(tr)
        return text

    def lemmat(self, line):
        res = [self.mystem.lemmatize(word.lower())[0] for word in line.split()]
        return res
