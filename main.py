#!/usr/bin/env python3
"""Sentiment and other analysis of top 100 song lyrics

TODO
- load info into db for faster queries

"""

from bs4 import BeautifulSoup
from textblob import TextBlob
from urllib.parse import urlparse
import csv
import matplotlib.pyplot as plt
import numpy as np
import operator
import os.path
import sys
import time
import urllib.request


MISSING_LYRICS = "Unfortunately, we aren't authorized to display these lyrics"


def main():
    top100_report = "top100" in sys.argv
    genre_report = "genre" in sys.argv
    if top100_report:
        index_urls = ["http://www.metrolyrics.com/top100.html"]
    elif genre_report:
        index_urls = [
            "http://www.metrolyrics.com/top100-country.html",
            "http://www.metrolyrics.com/top100-electronic.html",
            "http://www.metrolyrics.com/top100-folk.html",
            "http://www.metrolyrics.com/top100-hiphop.html",
            "http://www.metrolyrics.com/top100-indie.html",
            "http://www.metrolyrics.com/top100-jazz.html",
            "http://www.metrolyrics.com/top100-metal.html",
            "http://www.metrolyrics.com/top100-pop.html",
            "http://www.metrolyrics.com/top100-rb.html",
            "http://www.metrolyrics.com/top100-rock.html",
        ]
    else:
        print("Help: Args <top100|genre>")
        return

    analysis, all_lyrics, lyrics_by_genre = get_data(index_urls)

    if genre_report:
        generate_genre_report(lyrics_by_genre)

    elif top100_report:
        generate_top100_report(analysis, all_lyrics)

    plt.show()


def get_data(index_urls):
    links = []
    for index_url in index_urls:
        if not lyrics_html_exist(index_url):
            download_webpage(index_url)

        genre = get_genre(index_url)
        links.extend(
            [(l, genre) for l in get_lyrics_links(read_cached_webpage(index_url))]
        )

    lyrics_by_genre = {}

    analysis = []
    all_lyrics = ""
    for song_url, genre in links:
        if not lyrics_html_exist(song_url):
            download_webpage(song_url)

        if not lyrics_text_exist(song_url):
            title, lyric_text = get_lyric_text(read_cached_webpage(song_url))
            write_lyric_text(title, lyric_text, song_url)

        title, lyric_text = read_cached_text(song_url)
        if lyric_text == MISSING_LYRICS:
            continue

        analysis.append(LyricsContainer(title, song_url, lyric_text, genre))
        if genre:
            if genre not in lyrics_by_genre:
                lyrics_by_genre[genre] = ""
            lyrics_by_genre[genre] += lyric_text + "\n"

        all_lyrics += lyric_text + "\n"

    return analysis, all_lyrics, lyrics_by_genre


def generate_top100_report(analysis, all_lyrics):
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

    # Top words
    top_words = sorted(
        all_lyrics_blob.word_counts.items(), reverse=True, key=operator.itemgetter(1)
    )
    top_words = [word for word in top_words if len(word[0]) > 4][0:10]
    build_bar_chart(
        tuple([word[1] for word in top_words]),
        "Word",
        "Count",
        "Most used words where len > 4",
        labels=[word[0] for word in top_words],
    )

    # Most used tags
    data = {}  # tag: count
    for t in all_lyrics_blob.tags:
        if t[1] in data:
            data[t[1]] += 1
        else:
            data[t[1]] = 1

    top_tags = sorted(data.items(), reverse=True, key=operator.itemgetter(1))[0:10]
    pos_lookup = get_pos()
    build_bar_chart(
        tuple([tag[1] for tag in top_tags]),
        "Tag",
        "Count",
        "Most used Tags",
        labels=["%s (%s)" % (pos_lookup[tag[0]], tag[0]) for tag in top_tags],
    )

    # Most positive or negative songs
    polarity_sort = sorted(
        analysis, key=lambda x: x.blob.sentiment.polarity, reverse=True
    )[0:10]

    polarity_sort_neg = sorted(analysis, key=lambda x: x.blob.sentiment.polarity)[0:10]
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
        tuple([a.blob.sentiment.polarity for a in polarity_sort_neg]),
        "Songs",
        "Polarity",
        "Most negative songs",
        labels=[a.title() for a in polarity_sort_neg],
    )

    # Most Subjective songs
    build_bar_chart(
        tuple([a.blob.sentiment.subjectivity for a in subjectivity_sort]),
        "Songs",
        "Subjectivity",
        "Most Subjective songs",
        labels=[a.title() for a in subjectivity_sort],
    )


def generate_genre_report(lyrics_by_genre):
    blobs_by_genre = []
    for key in lyrics_by_genre.keys():
        blobs_by_genre.append([key, TextBlob(lyrics_by_genre[key])])

    polarity_sort = sorted(
        blobs_by_genre, key=lambda x: x[1].sentiment.polarity, reverse=True
    )

    build_bar_chart(
        tuple([a[1].sentiment.polarity for a in polarity_sort]),
        "Genre",
        "Polarity",
        "Polarity by Genre",
        labels=[a[0].capitalize() for a in polarity_sort],
    )


def elapsedTime(start, label):
    end = time.time()
    elapsed = end - start
    print("%s: %s" % (label, elapsed))
    return end


def get_pos():
    pos_lookup = {}
    with open("pos.txt") as tsv:
        for line in csv.reader(tsv, dialect="excel-tab"):
            pos_lookup[line[1]] = line[2]
    return pos_lookup


def build_bar_chart(data, ylabel, xlabel, title, labels=None):
    n_groups = len(data)
    _, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.35
    opacity = 0.5
    ax.bar(index, data, bar_width, alpha=opacity, color="b")
    ax.set_xlabel(ylabel)
    ax.set_ylabel(xlabel)
    ax.set_title(title)
    if labels:
        ax.set_xticks(index)
        ax.set_xticklabels(labels, rotation="vertical")
    plt.subplots_adjust(bottom=0.4)
    return


class LyricsContainer:

    def __init__(self, title, url, lyric_text, genre):
        self._title = title
        self.blob = TextBlob(lyric_text)
        self.url = url
        self.lyric_text = lyric_text
        self.genre = genre

    def title(self):
        if self.genre:
            return "%s (%s)" % (self._title, self.genre)
        else:
            return self._title

    def __str__(self):
        return "Title: %s, Genre: %s, URL: %s" % (self.title(), self.genre, self.url)


def read_cached_text(url):
    filename = filename_from_url(url)
    with open("lyrics_text/" + filename + ".txt") as fo:
        title = fo.readline().replace("\n", "")
        content = fo.read()
        return title, content


def get_lyrics_links(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    found = soup.find_all(lyrics_link)
    return [l["href"] for l in found]


def get_genre(index_url):
    filename = filename_from_url(index_url)
    if "-" in filename:
        return filename.split("-")[1].replace(".html", "")
    return ""


def get_lyric_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    lyrics = soup.find_all(class_="verse")
    content = ""
    for lyr in lyrics:
        content += lyr.get_text()
    found = soup.find_all("h1")
    return found[0].get_text().replace("Lyrics", "").strip(), content


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


def write_lyric_text(title, content, url):
    filename = filename_from_url(url)
    fo = open("lyrics_text/" + filename + ".txt", "w")
    fo.write(title + "\n" + content)
    fo.close()


if __name__ == "__main__":
    main()
    sys.exit(0)
