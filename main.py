#!/usr/bin/env python3
"""Sentiment and other analysis of top 100 song lyrics"""

import sys
import urllib.request
from urllib.parse import urlparse
import os.path
from bs4 import BeautifulSoup

from textblob import TextBlob

import matplotlib.pyplot as plt

import numpy as np
import operator


def main():
    index_url = "http://www.metrolyrics.com/top100.html"
    if not lyrics_html_exist(index_url):
        download_webpage(index_url)

    links = get_lyrics_links(read_cached_webpage(index_url))

    analysis = []
    for song_url in links:
        if not lyrics_html_exist(song_url):
            download_webpage(song_url)

        if not lyrics_text_exist(song_url):
            write_lyric_text(get_lyric_text(read_cached_webpage(song_url)), song_url)

        lyric_text = read_cached_text(song_url)
        blob = TextBlob(lyric_text)
        la = LyricsAnalysis(blob.sentiment, blob.word_counts, blob.tags, lyric_text)
        analysis.append(la)

    fig1 = build_bar_chart(
        tuple([a.sentiment.polarity for a in analysis]),
        "Polarity",
        "Songs",
        "Lyric Polarity by Song",
    )
    fig2 = build_bar_chart(
        tuple([a.sentiment.subjectivity for a in analysis]),
        "Subjectivity",
        "Songs",
        "Lyric Subjectivity by Song",
    )

    all_lyrics = "\n".join([a.lyric_text for a in analysis])
    blob = TextBlob(all_lyrics)
    top_words = sorted(
        blob.word_counts.items(), reverse=True, key=operator.itemgetter(1)
    )[0:10]

    fig3 = build_bar_chart(
        tuple([word[1] for word in top_words]),
        "Word",
        "Count",
        "Word Count Analysis",
        labels=[word[0] for word in top_words],
    )

    fig3.show()


def build_bar_chart(data, ylabel, xlabel, title, labels=None):
    n_groups = len(data)
    _, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.35
    opacity = 0.4
    ax.bar(index, data, bar_width, alpha=opacity, color="b")
    ax.set_xlabel(ylabel)
    ax.set_ylabel(xlabel)
    ax.set_title(title)
    ax.set_xticks(index)
    if labels:
        ax.set_xticklabels(labels)
    return plt


class LyricsAnalysis:

    def __init__(self, sentiment, word_counts, tags, lyric_text):
        self.sentiment = sentiment
        self.word_counts = word_counts
        self.tags = tags
        self.lyric_text = lyric_text

    def __str__(self):
        return "pol: %s, sub: %s, wc len: %s, tags len: %s" % (
            self.sentiment.polarity,
            self.sentiment.subjectivity,
            len(self.word_counts),
            len(self.tags),
        )


def read_cached_text(url):
    filename = filename_from_url(url)
    fo = open("lyrics_text/" + filename + ".txt")
    content = fo.read()
    fo.close()
    return content


def get_lyrics_links(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    found = soup.find_all(lyrics_link)
    links = [l["href"] for l in found]
    return links


def get_lyric_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    lyrics = soup.find_all(class_="verse")
    content = ""
    for lyr in lyrics:
        content += lyr.get_text()
    return content


def lyrics_link(tag):
    return (
        tag.name == "a"
        and tag.has_attr("class")
        and ("song-link" in tag["class"] or "title" in tag["class"])
    )


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


if __name__ == "__main__":
    main()
    sys.exit(0)
