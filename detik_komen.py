from json import JSONDecoder
from scrapy.crawler import CrawlerProcess

import requests
import scrapy
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--count', help='# of comments grabbed per post, default: 9999', type=int, default=9999)
parser.add_argument('-p', '--page', help='# of pages crawled, default: 0 (all page)', type=int, default=0)
parser.add_argument('-s', '--start', help='start from this page number, default: 1', type=int, default=1)
parser.add_argument('-d', '--delay', help='delay between crawl (in seconds), default: 0', type=int, default=0)
args = parser.parse_args()
if args.delay is not None:
    delay = args.delay


class CommentSpider(scrapy.Spider):
    name = "detik"
    history = {}
    current_page_domain = 'https://www.detik.com/pemilu/'
    current_page_num = ''
    comment_count = 9999
    page_count = 0
    start_from = 1
    if args.count is not None:
        comment_count = args.count
    if args.page is not None:
        page_count = args.page
    if args.start is not None:
        start_from = args.start
        current_page_num = args.start
    start_urls = [
        'https://www.detik.com/pemilu/' + str(start_from),
    ]

    def parse(self, response):
        try:
            page_id = response.css('div.paging_ a.selected::attr(href)').extract_first()
            self.current_page_domain = page_id[:29]
            self.current_page_num = page_id[29:]
        except:
            page_id = None

        print('==============BEGIN=================')
        print(self.current_page_domain + str(self.current_page_num))
        if response.status == 302:
            print('====================================')
            print('Redirect detected, waiting 5 seconds to retry')
            print('====================================')
            time.sleep(5)
            yield scrapy.Request(self.current_page_domain + str(self.current_page_num), self.parse, dont_filter=True)

        # buka file history untuk melihat progress sebelumnya (jika ada)
        try:
            with open('history.csv', 'r') as history_file:
                for line in history_file:
                    line_part = line.split(';')
                    self.history[line_part[0]] = line_part[1]
        except: pass

        # mulai crawl
        if page_id is None:
            return
        print('====================================')
        print('start from page = ' + str(self.start_from))
        print('current page = ' + page_id)
        print('# of page to crawl = ' + str(self.page_count))
        print('# of comments to fetch = ' + str(self.comment_count))
        print('====================================')
        for article in response.css('ul.feed article'):
            url = article.css('a::attr(href)').extract_first()
            url = url.split('//')
            url_part = url[1].split('/')
            if url_part[1] == 'berita':
                url_part[2] = url_part[2][2:]
                self.get_next_page_comment(url_part[2])
                time.sleep(delay)

        # stop condition
        if page_id == 'https://www.detik.com/pemilu/' + str(self.page_count):
            print('====================================')
            print('Crawled ' + str(self.page_count) + ' latest page, stopping now')
            print('====================================')
            return

        # go to next page
        next_page = response.css('div.paging_ a.selected+a::attr(href)')
        yield scrapy.Request(next_page.extract_first(), self.parse, dont_filter=True)

    def get_next_page_comment(self, article_id):
        res = requests.get('https://newcomment.detik.com/graphql?query='
                           '{search(type:"comment",size:' + str(self.comment_count) + ',page:1,sort:"newest",'
                           'query:[{name:"news.artikel",terms:"' + article_id + '"},{name:"news.site",terms:"dtk"}]){'
                                                                                'paging counterparent hits{'
                                                                                'posisi results{'
                                                                                'id content news create_date}}}}')
        py_obj = JSONDecoder().decode(res.text)
        result = py_obj.get('data').get('search').get('hits').get('results')

        for r in result:
            with open('data.csv', 'a', encoding='utf-8') as myfile:
                if article_id in self.history:
                    if r.get('id') != self.history[article_id]:
                        try:
                            myfile.write(article_id + ';' + r.get('news').get('date') + ';' + r.get('content') + ';'
                                         + r.get('create_date') + '\n')
                        except: pass
                    else: break
                else:
                    try:
                        myfile.write(article_id + ';' + r.get('news').get('date') + ';' + r.get('content') + ';'
                                     + r.get('create_date') + '\n')
                        self.history[article_id] = r.get('id')
                    except:
                        pass

        with open('history.csv', 'w') as history_file:
            for key, value in self.history.items():
                history_file.write(key + ';' + value + ';\n')


process = CrawlerProcess({
    'DOWNLOAD_DELAY': delay,
    'DOWNLOADER_MIDDLEWARES': {
        # 'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
        # 'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware': None,
    },
    # 'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 302],
    'HTTPERROR_ALLOW_ALL': True,
})
process.crawl(CommentSpider)
process.start()

# stop condition for last page