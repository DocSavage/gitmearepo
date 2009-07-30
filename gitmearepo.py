#!/usr/bin/env python
#
"""
gitmearepo.py

Copyright (c) 2009 William T. Katz
Until August 30, 2009, noon PST, distributed under the Inverse MIT License.
After August 30, 2009, noon PST, distributed under the MIT License. 
See the README.textile file for more information on licensing.
"""
__author__ = 'William Katz'

import sys

UNKNOWN_LANGUAGE = 'Unknown'
DEFAULT_NUM_LINES = 1000

user_watching = {}      # Key: user id => Value: list of repo ids
user_langs = {}         # Key: user id => Value: dict of {language: # lines}
repo_headcount = {}     # Key: repo id => Value: # of watchers
repo_langs = {}         # Key: repo id => Value: list of (language, # lines) tuples.
languages = []
language_repos = {}     # Key: language => Value: list of (repo id, # watchers)

try:
    lang_file = open('lang.txt', 'r')
except IOError:
    sys.exit("Bleh.  Can't open lang.txt!")
finally:
    for line in lang_file:
        repo_id, lang_data = line.strip().split(':')
        repo_langs[repo_id] = []
        for lang_lines in lang_data.split(','):
            name, lines_str = lang_lines.split(';')
            repo_langs[repo_id].append((name, int(lines_str)))
            if name not in languages:
                languages.append(name)
    lang_file.close()

print "Language breakdown shows %d languages: %s" % \
      (len(languages), ', '.join(languages))

def add_to_user_prefs(user_id, repo_id):
    global repo_languages, user_langs
    if user_id not in user_langs:
        user_langs[user_id] = {}
    if repo_id in repo_langs:
        lang_list = repo_langs[repo_id]
    else:
        lang_list = [(UNKNOWN_LANGUAGE, 0)]
    for lang_data in lang_list:
        lang, lines = lang_data
        user_langs[user_id][lang] = (user_langs[user_id].get(lang, 0) + lines)

try:
    data_file = open('data.txt', 'r')
except IOError:
    sys.exit("Bleh.  Can't open data.txt!")
finally:
    for line in data_file:
        user_id, repo_id = line.strip().split(':')
        add_to_user_prefs(user_id, repo_id)
        if user_id in user_watching:
            user_watching[user_id].append(repo_id)
        else:
            user_watching[user_id] = [repo_id]
        repo_headcount[repo_id] = (repo_headcount.get(repo_id, 0) + 1)
    data_file.close()

# Sort the repos in descending order of number of watchers
repo_list = repo_headcount.items()
repo_list.sort(key=lambda x: x[1], reverse=True)
print "Top 10 repos: %s" % (str(repo_list[:10]))

# For each language, get the top N repos where the repo is only in that
# language, javascript excluded
N = 10
HELPER_LANGS = ['JavaScript','ActionScript','Shell','Pure Data']
language_top_repos = {}
for repo_data in repo_list:
    repo_id, watchers = repo_data
    if repo_id not in repo_langs:
        repo_langs[repo_id] = [(UNKNOWN_LANGUAGE, DEFAULT_NUM_LINES)]
    for lang_data in repo_langs[repo_id]:
        lang, lines = lang_data
        if lang not in language_top_repos:
            language_top_repos[lang] = [repo_id]
        elif len(language_top_repos[lang]) < N:
            language_top_repos[lang].append(repo_id)

print "language_top_repos: %s" % (str(language_top_repos))

# Assume there's some kind of Long Tail for repository popularity.
# For each user, suggest the most popular repos for that user's
# favorite languages.
try:
    non_watcher = 0
    result_file = open('results.txt', 'w')
    test_file = open('test.txt', 'r')
    for line in test_file:
        user_id = line.strip()
        if user_id not in user_langs:
            non_watcher += 1
            # Since we have no clue about language or tastes, go with popular
            best_repos = [repo_id for repo_id, watchers in repo_list[:N]]
        else:
            lang_list = user_langs[user_id].items()
            lang_list.sort(key=lambda x: x[1], reverse=True)

            # Go through user's language in descending popularity
            # and find top repos until we get at least N.
            best_repos = []
            num = 0
            for lang_data in lang_list:
                lang, lines = lang_data
                for repo_id in language_top_repos[lang]:
                    if repo_id not in best_repos:
                        best_repos.append(repo_id)
                        if len(best_repos) >= N:
                            break
            # TODO -- Do something additional processing
        result_file.write("%s:%s\n" % (user_id, ','.join(best_repos[:N])))
except IOError:
    sys.exit("Had trouble writing results.")
finally:
    result_file.close()
    test_file.close()
    print "There were %d non-watchers among test users." % (non_watcher)
    