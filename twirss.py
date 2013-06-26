#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# licensed under the WTFPL

import sys; reload(sys); sys.setdefaultencoding('utf-8')
import tweepy
from string import Template
from locale import setlocale, LC_TIME
from cgi import escape
from re import findall, sub
from urllib import quote, FancyURLopener
from socket import setdefaulttimeout

CONSUMER_KEY = 'APPbntMLcMDuPwTahEJgA'
CONSUMER_SECRET = 'dZH2BChokybq8suqOJWwYZqV2J7UtTrFAglXeWyh0'

ACCESS_KEY = 'your access key'
ACCESS_SECRET = 'your secret key'

entry = Template('''<item>
    <title>${title}</title>
    <link>${link}</link>
    <description>${content}</description>
    <pubDate>${date}</pubDate>
    <guid>${link}</guid>
</item>''')

def process(text):
    '''process(text) takes a twitter message and unpack the url, links @user and links #hash'''
    
    def direct(url):
        '''bypasses horrible url shorteners'''
        setdefaulttimeout(2.5)
        FancyURLopener.version = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8'
        FancyURLopener.prompt_user_passwd = lambda self, host, realm: (None, None) # stolen from bytes.com (useful?)
        f = FancyURLopener()
        try:
            return f.open(url).geturl()
        except Exception: # FIXME: what exception could be raised? (IOError: setdefaulttimeout, )
            return url
    
    def url(text):
        for item in findall('https?://[\w\d/?=#-.~]+', text):
            '''TODO: we need a really good url matching regex'''
            real = direct(item)
            text = text.replace(item, '<a href="%s">%s</a>' % (real, real))
        return text
            
    def at(text):
        '''converts @user to <a href="http://twitter.com/user">@user</a>'''
        return sub(r'@([\w\d_]+)', r'<a href="http://twitter.com/\1">@\1</a>', text)
        
    def hash(text):
        '''converts #hash to <a href="http://twitter.com/search?q=#hash">#hash</a>'''
        return sub(r'(#[\w\d]+)', r'<a href="http://twitter.com/search?q=\1">\1</a>', text)
        
    text = url(text)
    text = at(text)
    text = hash(text)
    
    return text

if __name__ == '__main__':

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)

    Timeline = api.home_timeline(count=50)
    _home = api.me().screen_name
    setlocale(LC_TIME, 'C') # tweepy fix

    print 'Content-Type: application/atom+xml\n'
    print '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">'
    print '<channel>'
    print '     <title>Timeline: %s</title>' % _home
    print '     <link>http://twitter.com/%s</link>' % _home
    print '     <description>twirss - a simple tweet-to-atom feed aggregator</description>'
    print '     <language>de-DE</language>' # FIXME: there is something like locale.getlocale...
    print '<pubDate>%s</pubDate>' % Timeline[0].created_at.strftime('%a, %d %b %Y %H:%M:%S GMT') # last update
    print '<atom:link href="/" rel="self" type="application/rss+xml" />'
    
    for Tweet in Timeline:
        _author = Tweet.author.screen_name
        _text = Tweet.text
        title = '%s: %s' % (_author, _text)
        link = 'http://twitter.com/%s/status/%s' % (_author, Tweet.id)
        content = '<a href="http://twitter.com/%s"><b>%s</b></a>: %s' % (_author, _author, process(_text))
        date = Tweet.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        print entry.safe_substitute({'title': escape(title), 'link': link, 'content': escape(content), 'date': date})
        
    print '</channel>'
    print '</rss>'