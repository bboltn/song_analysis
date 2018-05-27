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
    all_lyrics = ""
    for song_url in links:
        if not lyrics_html_exist(song_url):
            download_webpage(song_url)

        if not lyrics_text_exist(song_url):
            write_lyric_text(get_lyric_text(read_cached_webpage(song_url)), song_url)

        lyric_text = read_cached_text(song_url)
        analysis.append(LyricsContainer(song_url, lyric_text))
        all_lyrics += lyric_text + "\n"

    build_bar_chart(
        tuple([a.blob.sentiment.polarity for a in analysis]),
        "Polarity",
        "Songs",
        "Lyric Polarity by Song",
    )

    build_bar_chart(
        tuple([a.blob.sentiment.subjectivity for a in analysis]),
        "Subjectivity",
        "Songs",
        "Lyric Subjectivity by Song",
    )

    all_lyrics_blob = TextBlob(all_lyrics)
    top_words = sorted(
        all_lyrics_blob.word_counts.items(), reverse=True, key=operator.itemgetter(1)
    )[0:10]

    build_bar_chart(
        tuple([word[1] for word in top_words]),
        "Word",
        "Count",
        "Word Count Analysis",
        labels=[word[0] for word in top_words],
    )

    data = {}  # tag: count
    for t in all_lyrics_blob.tags:
        if t[1] in data:
            data[t[1]] += 1
        else:
            data[t[1]] = 1

    top_tags = sorted(data.items(), reverse=True, key=operator.itemgetter(1))[0:10]

    build_bar_chart(
        tuple([tag[1] for tag in top_tags]),
        "Tag",
        "Count",
        "Most used Tags",
        labels=[tag[0] for tag in top_tags],
    )

    # polarity is whether the expressed opinion in the text is positive, negative, or
    # neutral

    polarity_sort = sorted(
        analysis, key=lambda x: x.blob.sentiment.polarity, reverse=True
    )[0:10]
    subjectivity_sort = sorted(
        analysis, key=lambda x: x.blob.sentiment.subjectivity, reverse=True
    )[0:10]

    build_bar_chart(
        tuple([a.blob.sentiment.polarity for a in polarity_sort]),
        "Songs",
        "Polarity",
        "Most positive songs",
        labels=[a.title() for a in polarity_sort],
    )

    build_bar_chart(
        tuple([a.blob.sentiment.subjectivity for a in subjectivity_sort]),
        "Songs",
        "Subjectivity",
        "Most Subjective songs",
        labels=[a.title() for a in subjectivity_sort],
    )
    plt.show()

    # Most negative (polarity) songs
    # Least Subjective (subjectivity) songs


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
        ax.set_xticklabels(labels, rotation="vertical")


class LyricsContainer:

    def __init__(self, url, lyric_text):
        self.blob = TextBlob(lyric_text)
        self.url = url
        self.lyric_text = lyric_text

    def title(self):
        return (
            filename_from_url(self.url)
            .replace("-", " ")
            .replace(".html", "")[0:20]
            .capitalize()
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
