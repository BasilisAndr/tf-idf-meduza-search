import justext
import requests
# nlp tools / similarity metrics
from sklearn.feature_extraction.text import TfidfVectorizer
from bs4 import BeautifulSoup as BS
import re
import os
import json
from classes import LinkQ, Text

"""
Скачивание некоторого набора страниц (+ переход по ссылкам) check
Удаление навигационной обвязки check
Лемматизация (?) check
Сохранение обратного индекса check
Поиск подходящих документов по обратному индексу check
Ранжирование check
"""


def get_links(page, url):
    page = BS(page, "html.parser")
    links = []
    for li in page('a'):
        try:
            if not li["href"].startswith("mailto:"):
                links.append(re.sub('\\\\', '/', li["href"]))
        except:
            pass
    links = link_check(links, url.split('/'))
    global load_q
    load_q.add_links(links)
    return links


def link_check(links, parts):
    for li in range(len(links)):
        if not links[li].startswith('http'):
            if not links[li].startswith('..'):
                if not links[li].startswith('/'):
                    links[li] = '/'.join(parts[:-1] + [links[li]])
                elif links[li].startswith('//'):
                    links[li] = 'https:{}'.format(links[li])
                else:
                    links[li] = '/'.join(parts[:3] + [links[li][1:]])
            else:
                up = re.findall('\.\.', links[li])
                links[li] = '/'.join(parts[:(-1 - len(up))] + links[li].split('/')[len(up):])
    return links


def get_text(url):
    r = requests.get(url)
    text = r.text
    get_links(text, url)
    extracted_text = '\n'.join(p.text for p in justext.justext(r.text, justext.get_stoplist('Russian')) \
                               if not p.is_boilerplate)
    # tfidf_vectorizer = TfidfVectorizer(stop_words=['в', 'на', 'и'])
    # tfidf_article = tfidf_vectorizer.fit_transform([extracted_text])
    # print(tfidf_vectorizer.vocabulary_)
    return extracted_text


def handle_text(text, i, url):
    if not os.path.exists('./src/lemm'):
        os.makedirs('./src/lemm')
    with open('./src/lemm/page_{}_l.txt'.format(i), 'w') as f:
        f.write(url + '\n')
        f.write(Tee.normalize(text))
    with open('./src/page_{}.txt'.format(i), 'w') as f:
        f.write(url + '\n')
        f.write(text)
    with open('docindices.txt', 'a') as f:
        f.write('{} : {}\n'.format(url, i))


def make_index():
    index = {}
    for root, dirs, files in os.walk('./src/lemm'):
        for fil in files:
            with open(os.path.join(root, fil)) as f:
                lines = f.readlines()
                if len(lines) > 1:
                    name = lines[0].strip()
                    text = ' '.join(lines[1:])
                    text = re.sub('  +', ' ', text)
                    for word in text.split():
                        if word in index:
                            index[word].append(name)
                        else:
                            index[word] = [name]
    for ind in index:
        index[ind] = list(set(index[ind]))
    with open('1index.json', 'w') as f:
        json.dump(index, f)


def prepare():
    if os.path.exists('docindices.txt'):
        os.remove('docindices.txt')
    for i in load_q.links:
        page = get_text(i)
        handle_text(page, load_q.links.index(i), i)
        if len(load_q.links) > 500:
            break
    print(len(load_q.links))
    make_index()


def open_dependencies():
    with open('1index.json') as f:
        index = json.load(f)
    with open('docindices.txt') as f:
        doc_ind = {line.split(' : ')[0].strip(): line.split(' : ')[1].strip() for line in f.readlines()}
    return index, doc_ind


def process_query(index, doc_ind, query):
    doc_names = []
    for word in query:
        if word in index:
            doc_names += [(doc_ind.get(url), url) for url in index.get(word)]
    if doc_names == []:
        print("Ничего не нашлось.(")
    return list(set(doc_names))


def tfidfmag(doc_names, query):
    docs = [open('./src/lemm/page_{}_l.txt'.format(num[0])).read() for num in doc_names]
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform([' '.join(query)] + docs)
    pairwise_similarity = tfidf_matrix * tfidf_matrix.T
    print_similarity(pairwise_similarity.A)
    return pairwise_similarity.A


def ranger(matrix, doc_names):
    sims = [matrix[0, i] for i in range(1,matrix[0].shape[0])]
    relev_sort = sorted(zip(sims, doc_names), reverse=True)
    return relev_sort


def print_similarity(matrix):
    for i in range(1,matrix[0].shape[0]):
        print('Similariry between item 1 and %d = %.6f' % (i + 1, matrix[0, i]))


def main():
    index, doc_ind = open_dependencies()
    while True:
        query = input("Q: ")
        if query == "":
            break
        query = Tee.lemmat(query)
        doc_names = process_query(index, doc_ind, query)
        matrix = tfidfmag(doc_names, query)
        for i in ranger(matrix, doc_names):
            print(i[1][1])


# load_q = LinkQ('http://chords.auctyon.ru/true/index.html')
if __name__ == '__main__':
    # load_q = LinkQ('https://meduza.io/')
    Tee = Text()
    # prepare()
    # make_index()
    main()

