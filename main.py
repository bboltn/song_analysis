#!/usr/bin/env python3

import sys
import urllib.request
import os.path
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def main():
    url = "http://www.metrolyrics.com/top100.html"
    if not lyrics_html_exist(url):
        download_webpage(url)
    content = read_cached_webpage(url)

    soup = BeautifulSoup(content, 'html.parser')

    found = soup.find_all(lyrics_link)
    links = [l['href'] for l in found]
    for l in links:
        if not lyrics_html_exist(l):
            download_webpage(l)
        
        if not lyrics_text_exist(l):
            content = read_cached_webpage(l)
            soup = BeautifulSoup(content, 'html.parser')
            lyrics = soup.find_all(class_="verse")
            content = ""
            for lyr in lyrics:
                content += lyr.get_text()
            write_lyric_text(content, l)

def lyrics_link(tag):
    return tag.name == "a" and tag.has_attr('class') and ("song-link" in tag['class'] or "title" in tag['class'])

def filename_from_url(url):
    parsed = urlparse(url)
    return os.path.basename(parsed.path)

def lyrics_html_exist(url):
    filename = filename_from_url(url)
    return os.path.exists("lyrics/" + filename)

def lyrics_text_exist(url):
    filename = filename_from_url(url)
    return os.path.exists("lyrics_text/" + filename + ".txt")

def download_webpage(url):
    filename = filename_from_url(url)
    web_page = urllib.request.urlopen(url)
    content = web_page.read()
    fo = open("lyrics/" + filename, "wb")
    fo.write(content)
    fo.close()

def read_cached_webpage(url):
    filename = filename_from_url(url)
    fo = open("lyrics/" + filename)
    content = fo.read()
    fo.close()
    return content    

def write_lyric_text(content, url):
    filename = filename_from_url(url)
    fo = open("lyrics_text/" + filename + ".txt", "w")
    fo.write(content)
    fo.close()

if __name__ == '__main__':
    main()
    sys.exit(0)