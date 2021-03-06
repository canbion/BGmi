# coding: utf-8
from __future__ import print_function, unicode_literals

import os

from bgmi.config import SAVE_PATH, FRONT_STATIC_PATH
from bgmi.front.base import BaseHandler, COVER_URL
from bgmi.models import STATUS_NORMAL, STATUS_UPDATING, STATUS_END, Followed
from bgmi.utils import normalize_path


def get_player(bangumi_name):
    episode_list = {}
    bangumi_path = os.path.join(SAVE_PATH, bangumi_name)
    for root, _, files in os.walk(bangumi_path):
        _ = root.replace(bangumi_path, '').split(os.path.sep)
        base_path = root.replace(SAVE_PATH, '')
        if len(_) >= 2:
            episode_path = root.replace(os.path.join(SAVE_PATH, bangumi_name), '')
            if episode_path.split(os.path.sep)[1].isdigit():
                episode = int(episode_path.split(os.path.sep)[1])
            else:
                continue
        else:
            episode = -1

        for bangumi in files:
            if any([bangumi.lower().endswith(x) for x in ['.mp4', '.mkv']]):
                video_file_path = os.path.join(base_path, bangumi)
                video_file_path = os.path.join(os.path.dirname(video_file_path), os.path.basename(video_file_path))
                video_file_path = video_file_path.replace(os.path.sep, '/')
                episode_list[episode] = {'path': video_file_path}
                break

    return episode_list


class IndexHandler(BaseHandler):
    def get(self, path):
        if not os.path.exists(FRONT_STATIC_PATH):
            msg = '''<h1>Thanks for your using BGmi</h1>
            <p>It seems you have not install BGmi Frontend, please run <code>bgmi install</code> to install.</p>
            '''
            self.write(msg)
            self.finish()
        else:
            if not path:
                path = 'index.html'

            p = os.path.abspath(os.path.join(FRONT_STATIC_PATH, path))

            if not os.path.isfile(p) or not p.startswith(FRONT_STATIC_PATH):
                return self.write_error(404)

            ext = os.path.splitext(p)[1].lower()
            if ext == '.js':
                self.set_header('content-type', 'application/javascript')
            elif ext == '.css':
                self.set_header('content-type', 'text/css')

            with open(p, 'rb') as f:
                self.write(f.read())
                self.finish()


class BangumiListHandler(BaseHandler):
    def get(self, type_=''):
        data = Followed.get_all_followed(STATUS_NORMAL, STATUS_UPDATING if not type_ == 'old' else STATUS_END)

        if type_ == 'index':
            data.extend(self.patch_list)
            data.sort(key=lambda _: _['updated_time'] if _['updated_time'] else 1)

        for bangumi in data:
            bangumi['cover'] = '{}/{}'.format(COVER_URL, normalize_path(bangumi['cover']))

        data.reverse()

        for item in data:
            item['player'] = get_player(item['bangumi_name'])

        self.write(self.jsonify(data))
        self.finish()
