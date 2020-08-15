'''
Modified from Github user deepanprabhu
(Deepan Prabhu Babu)

Original repo
https://github.com/deepanprabhu/duckduckgo-images-api

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org>
'''
import os, random, requests, re, json, time, logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, String, Date, Boolean,LargeBinary
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.sql import exists


Base = declarative_base()
ENGINE = create_engine('sqlite:///cache.db')

class CacheItem(Base):
    __tablename__ = 'cacheitems'
    key = Column(String(2048), primary_key=True)
    data = Column(LargeBinary())

Base.metadata.create_all(ENGINE)
Session = sessionmaker(bind=ENGINE)

#logging.basicConfig(level=logging.DEBUG);
logger = logging.getLogger(__name__)

def dl_url(url, filename):
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception(str(r.status_code))
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)

# returns whether cache was hit
def dl_first_image(query, filename):
    session = Session()
    if session.query(exists().where(CacheItem.key == query)).scalar():
        print('Cache hit for', query)
        f = open(filename, 'wb')
        f.write(session.query(CacheItem.data).filter(CacheItem.key == query).scalar())
        f.close()
        return filename, True
    search_results = search(query + ' ' + '-youtube.com')
    if len(search_results) == 0:
        return None, False
    urls = [r['image'] for r in search_results]
    for url in urls:
        try:
            dl_url(url, filename)
            f = open(filename, 'rb')
            data = f.read()
            f.close()
            session.add(CacheItem(key=query, data=data))
            session.commit()
            return filename, False
        except Exception as e:
            print('got error {} trying {}'.format(e, url))

def search(keywords):
    url = 'https://duckduckgo.com/';
    params = {
    	'q': keywords
    };

    logger.debug("Hitting DuckDuckGo for Token");

    #   First make a request to above URL, and parse out the 'vqd'
    #   This is a special token, which should be used in the subsequent request
    res = requests.post(url, data=params)
    searchObj = re.search(r'vqd=([\d-]+)\&', res.text, re.M|re.I);

    if not searchObj:
        logger.error("Token Parsing Failed !");
        return -1;

    logger.debug("Obtained Token");

    headers = {
        'authority': 'duckduckgo.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'sec-fetch-dest': 'empty',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'referer': 'https://duckduckgo.com/',
        'accept-language': 'en-US,en;q=0.9',
    }

    params = (
        ('l', 'us-en'),
        ('o', 'json'),
        ('q', keywords),
        ('vqd', searchObj.group(1)),
        ('f', ',,,'),
        ('p', '1'),
        ('v7exp', 'a'),
    )

    requestUrl = url + "i.js";

    logger.debug("Hitting Url : %s", requestUrl);

    while True:
        try:
            res = requests.get(requestUrl, headers=headers, params=params);
            results = json.loads(res.text);
            try:
                results = results['results']
                print('num results', len(results))
                return results
            except KeyError:
                return None
        except ValueError as e:
            logger.debug("Hitting Url Failure - Sleep and Retry: %s", requestUrl);
            time.sleep(5);
            continue;

def printJson(objs):
    for obj in objs:
        print("Width {0}, Height {1}".format(obj["width"], obj["height"]));
        print("Thumbnail {0}".format(obj["thumbnail"]));
        print("Url {0}".format(obj["url"]));
        print("Title {0}".format(obj["title"].encode('utf-8')));
        print("Image {0}".format(obj["image"]));
        print("__________");
