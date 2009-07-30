#!/usr/bin/env python
#
"""
gitmearepo.py

Copyright (c) 2009 William T. Katz
Until August 30, 2009, noon PST, distributed under the Inverse MIT License.
After August 30, 2009, noon PST, distributed under the MIT License. 
See the README.textile file for more information on licensing.

This program explores the repository data released by github and may eventually
try to make some recommendations.
"""
__author__ = 'William Katz'

import sys

UNKNOWN_LANGUAGE = 'Unknown'
DEFAULT_NUM_LINES = 1000

user_watching = {}      # Key: user id => Value: list of repo ids
repo_data = {}          # Key: repo id => Value: (username, repo name, primary language, fork repo id)
repo_headcount = {}     # Key: repo id => Value: # of watchers
repo_langs = {}         # Key: repo id => Value: list of (language, # lines) tuples.
languages = []
language_repos = {}     # Key: language => Value: list of (repo id, # watchers)

lang_file = open('lang.txt', 'r')
try:
    for line in lang_file:
        repo_id, lang_data = line.strip().split(':')
        repo_langs[repo_id] = []
        for lang_lines in lang_data.split(','):
            name, lines_str = lang_lines.split(';')
            repo_langs[repo_id].append((name, int(lines_str)))
            if name not in languages:
                languages.append(name)
finally:
    lang_file.close()

print "Language breakdown shows %d languages: %s" % \
      (len(languages), ', '.join(languages))

def repo_info(repo_id):
    global repo_data
    if not repo_id:
        return 'None'
    repo_datum = repo_data[repo_id]
    text = "%s (primary language: %s, fork from %s)" % \
           ('/'.join(repo_datum[:2]), str(repo_datum[2]), repo_info(repo_datum[3]))
    return text

repo_file = open('repos.txt', 'r')
try:
    for line in repo_file:
        repo_id, repo_text = line.strip().split(':')
        parts = repo_text.split(',')
        user_name, repo_name = parts[0].split('/')
        forked_id = parts[-1] if len(parts) > 2 else None
        main_lang = None
        if repo_id in repo_langs:
            lang_list = repo_langs[repo_id]
            lang_list.sort(key=lambda x: x[1], reverse=True)
            if len(lang_list) < 2 or lang_list[0][1] > 2 * lang_list[1][1]:
                main_lang = lang_list[0][0]
            else:
                main_lang = None
        repo_data[repo_id] = (user_name, repo_name, main_lang, forked_id)
finally:
    repo_file.close()

data_file = open('data.txt', 'r')
try:
    for line in data_file:
        user_id, repo_id = line.strip().split(':')
        if user_id in user_watching:
            user_watching[user_id].append(repo_id)
        else:
            user_watching[user_id] = [repo_id]
        repo_headcount[repo_id] = (repo_headcount.get(repo_id, 0) + 1)
finally:
    data_file.close()

# Sort the repos in descending order of number of watchers
repo_list = repo_headcount.items()
repo_list.sort(key=lambda x: x[1], reverse=True)
print "Top 10 repos:"
for watch_data in repo_list[:10]:
    repo_id, watchers = watch_data
    print repo_info(repo_id), "with", watchers, "watchers"

# For each language, get the top N repos that are mostly
# in one type of language
N = 10
language_top_repos = {}
for watch_data in repo_list:
    repo_id, watchers = watch_data
    primary_language = repo_data[repo_id][2]
    if primary_language:
        if primary_language not in language_top_repos:
            language_top_repos[primary_language] = [repo_id]
        elif len(language_top_repos[primary_language]) < N:
            language_top_repos[primary_language].append(repo_id)

print "\nTop repositories by language:"
for lang in language_top_repos:
    print lang, "(%d)" % (len(language_top_repos[lang]))
    for repo_id in language_top_repos[lang]:
        print "-", repo_info(repo_id)

# Assume there's some kind of Long Tail for repository popularity.
# For each user, suggest the most popular repos for that user's
# favorite languages.
default_best_repos = [repo_id for repo_id, watchers in repo_list[:N]]
favorite_languages = {}
non_watcher = 0
result_file = open('results.txt', 'w')
test_file = open('test.txt', 'r')
try:
    for line in test_file:
        user_id = line.strip()
        if user_id not in user_watching:
            non_watcher += 1
            best_repos = default_best_repos
        else:
            languages = {}
            for repo_id in user_watching[user_id]:
                lang = repo_data[repo_id][2]
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
            if not languages:
                best_repos = default_best_repos
            else:
                lang_list = languages.items()
                lang_list.sort(key=lambda x: x[1], reverse=True)

                lang, times = lang_list[0]
                if times == 0:
                    best_repos = default_best_repos
                else:
                    favorite_languages[lang] = favorite_languages.get(lang, 0) + 1
                    # Go through user's language in descending popularity
                    # and find top repos until we get at least N.
                    best_repos = []
                    num = 0
                    for lang_data in lang_list:
                        lang, times = lang_data
                        for repo_id in language_top_repos[lang]:
                            if repo_id not in best_repos:
                                best_repos.append(repo_id)
                                if len(best_repos) >= N:
                                    break
        result_file.write("%s:%s\n" % (user_id, ','.join(best_repos[:N])))
finally:
    result_file.close()
    test_file.close()
    
print "There were %d non-watchers among test users." % (non_watcher)

language_list = favorite_languages.items()
language_list.sort(key=lambda x: x[1], reverse=True)

print "List of favorite languages by line count:"
for lang in language_list:
    print "%20s %8d users" % (lang[0], lang[1])
    