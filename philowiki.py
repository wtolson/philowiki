#!/usr/bin/env python
import sys
import json
import argparse

from os import path
from time import time

from urllib import unquote
from urlparse import urljoin, urlsplit

import requests
from lxml import html
from lxml import etree

class Cache(object):
    def __init__(self, exp_time=24*60*60, filename=None):
        self.exp_time = exp_time
        self.filename = filename
        self._cache   = {}

    @staticmethod
    def _normalize(filename):
        return path.abspath(path.expanduser(filename))

    @classmethod
    def open(cls, fp, **kwargs):
        if isinstance(fp, basestring):
            filename = cls._normalize(fp)

            if not path.isfile(filename):
                return cls(filename=filename, **kwargs)

            with open(filename) as fp:
                return cls.open(fp, filename=filename, **kwargs)

        cache = cls(**kwargs)

        for line in fp:
            cache.set(*json.loads(line))

        return cache

    def save(self, filename=None):
        if filename is None:
            filename = self.filename

        if isinstance(filename, basestring):
            with open(self._normalize(filename), 'w') as fp:
                return self.save(fp)

        for src, (dst, exp) in self._cache.iteritems():
            filename.write(json.dumps([src, dst, exp])+'\n')

    def set(self, src, dst, exp=None):
        if exp is None:
            exp = time()

        self._cache[src] = (dst, exp)

    def get(self, src):
        dst, exp = self._cache.get(src, (None, None))

        if dst is None:
            return None

        if exp + self.exp_time < time():
            return None

        return dst

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.save()


class Philowiki(object):
    def __init__(self,
        cache    = None,
        hostname = 'en.wikipedia.org',
    ):
        if cache is None:
            cache = Cache()

        self.cache    = cache
        self.hostname = hostname

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'PhiloWiki/1.1'})

    def get_page(self, title):
        params = {
            'action':   'mobileview',
            'format':   'json',
            'prop':     'text',
            'sections': 'all',
            'page':     title
        }

        resp = self.session.get(
            'http://%s/w/api.php' % self.hostname,
            params = params
        )

        if resp.status_code != requests.codes.ok:
            return None

        sections = resp.json()['mobileview']['sections']
        return '<div>%s</div>' % ''.join([s['text'] for s in sections])

    def normalize_title(self, title):
        if ':' in title:
            return None

        return title.replace(' ', '_')

    def find_link(self, content):
        return self._find_link(html.fromstring(content))

    def _extract_title(self, href):
        href = urlsplit(urljoin('http://%s/' % self.hostname, href))

        if href.hostname != self.hostname:
            return None

        if not href.path.startswith('/wiki/'):
            return None

        title = unquote(href.path[len('/wiki/'):])
        return self.normalize_title(title)

    def _find_link(self, el):
        if el.tag in ['table', 'i']:
            return

        for c in el.attrib.get('class', '').split():
            if c in ['dablink', 'tright', 'rellink', 'seealso']:
                return

        if el.attrib.get('id') == 'coordinates':
            return

        if el.tag == 'a':
            title = self._extract_title(el.attrib.get('href', ''))
            if title:
                return title

        for child in el.iterchildren(tag=etree.Element):
            title = self._find_link(child)

            if title is None:
                continue

            return title

    def _cache_key(self, title):
        return '%s:%s' % (self.hostname, title)

    def next_title(self, title):
        next = self.cache.get(self._cache_key(title))

        if next is not None:
            return next

        page = self.get_page(title)

        if page is None:
            return None

        next = self.find_link(page)
        if next is None:
            return None

        self.cache.set(self._cache_key(title), next)
        return next

    def crawl(self, title, destination='Philosophy'):
        title = self.normalize_title(title)
        if not title:
            print 'Not a valid page title'
            return

        count = 0
        history = []

        while title != destination:
            history.append(title)

            sys.stdout.write('%s -> ' % title)
            sys.stdout.flush()

            title = self.next_title(title)
            sys.stdout.write('%s\n' % title)

            if title is None:
                print 'Found dead end :('
                return

            if title in history:
                print 'Found infinate loop!'
                return

            count += 1

        print 'Found %s in %d steps!' % (destination, count)


def main():
    parser = argparse.ArgumentParser(description='It all leads to Philosophy.')

    parser.add_argument('start',
        metavar = 'START',
        help    = 'page to start at'
    )

    parser.add_argument('-e', '--end',
        default = 'Philosophy',
        help    = 'page to end at (default: Philosophy)'
    )

    parser.add_argument('-c', '--cache',
        default = '~/.philowikicache',
        help    = 'cache file (default: ~/.philowikicache)'
    )

    parser.add_argument('--exp',
        type    = int,
        default = 24*60*60,
        help    = 'experation time in seconds (default: 1 day)'
    )

    parser.add_argument('--host',
        default = 'en.wikipedia.org',
        help    = 'host to crawl (default: en.wikipedia.org)'
    )

    args = parser.parse_args()

    with Cache.open(args.cache, exp_time=args.exp) as cache:
        pw = Philowiki(cache, args.host)
        pw.crawl(args.start, args.end)

if __name__ == '__main__':
    main()
