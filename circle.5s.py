#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <bitbar.title>CircleCI Build Status</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Patrick Vilhena</bitbar.author>
# <bitbar.author.github>Nifengle</bitbar.author.github>
# <bitbar.desc>Shows the status of your CircleCI builds.</bitbar.desc>
# <bitbar.dependencies>python</bitbar.dependencies>

import os
import urllib2
import json
from operator import itemgetter

home_dir = os.path.expanduser('~')
token_path = '%s/.circle' % (home_dir)
circle_token = open(token_path, 'r').read().strip()

base_url = 'https://circleci.com/api/v1'
git_username = os.popen('git config user.username').readline().strip()

status_colors = {
    'failed': 'red',
    'success': 'green',
    'fixed': 'green',
    'running': '#66D3E4',
    'scheduled': 'purple',
    'not_running': 'purple',
    'timedout': 'yellow',
    'canceled': 'orange'
}

status_symbols = {
    'failed': u'\u2718 ',
    'success': u'\u2713',
    'fixed': u'\u2713',
    'running': u'\u25b6',
    'timedout': u'\u26A0',
    'scheduled': u'\u275a\u275a',
    'not_running': u'\u275a\u275a',
    'canceled': u'\u20e0'
}

def fetch_projects():
    url = '%s/projects?circle-token=%s' % (base_url, circle_token)
    request = urllib2.Request(url, headers = { 'Accept': 'application/json' })
    response = urllib2.urlopen(request).read()
    projects = json.loads(response)
    return projects

def user_branches():
    projects = fetch_projects()
    branches = {}
    for project in projects:
        for branch_name, branch_info in project['branches'].iteritems():
            if is_own_branch(branch_info):
                branch_info['reponame'] = project['reponame']
                branch_name = urllib2.unquote(branch_name).encode('utf-8')
                branches[branch_name] = branch_info

    return branches

def is_own_branch(branch):
    committer_usernames = branch.get('pusher_logins', '')
    return git_username in committer_usernames

def user_builds(branches):
    builds = []

    for name, info in branches.iteritems():
        if len(info.get('running_builds', [])) > 0:
            running_build = info['running_builds'][0]
            running_build['branch'] = name
            running_build['reponame'] = info['reponame']
            builds.append(running_build)

        if 'recent_builds' in info:
            for build in sorted(info['recent_builds'], key = itemgetter('build_num'), reverse = True):
                build['branch'] = name
                build['reponame'] = info['reponame']
                builds.append(build)
    return builds


def format_output(build, is_link = True):
    status = build['status']
    color = status_colors.get(status, 'yellow')
    symbol = status_symbols.get(status, u'\ufe0f')
    branch_name = build['branch'][:20]
    url = 'https://circleci.com/gh/usertesting/%s/%s' % (build['reponame'], build['build_num'])
    build_num = build['build_num']
    outcome = '%(symbol)s  %(branch_name)s - %(build_num)s | color=%(color)s' % locals()
    if is_link:
        outcome = '%(outcome)s href=%(url)s' % locals()
    return outcome.encode('utf-8')

if __name__ == '__main__':

    if len(circle_token) == 0:
        raise ValueError('Token can not be empty')

    user_branches = user_branches()
    user_builds = user_builds(user_branches)
    latest_builds = sorted(user_builds, key = itemgetter('build_num'), reverse = True)
    builds = latest_builds[:10]
    if len(builds) == 0:
        print 'No Builds'
    else:
        print format_output(builds[0], False)

        print '---'

        for build in builds:
            print format_output(build)
