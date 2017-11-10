# Copyright 2017, zhao, www.weizhao.info

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
a REST api server based on cherrypy
"""

import os
import sys
import argparse
import cherrypy
import router
from config import Config
import errorpage
from cherrypy.process.plugins import Daemonizer, PIDFile
import log
from auth import authentication

MYPATH = os.path.abspath(__file__)
MYDIR = os.path.dirname(MYPATH)
BACKUP_VER = "1.1"



def parse_cmdargs(args=None, target=''):
    AP = argparse.ArgumentParser
    parser = AP(description='backup dashboard and api server ', add_help=False)
    parser.add_argument('-h', '--help', help='show these help',
                        action='store_true')

    parser.add_argument('-c', '--conf', dest='backupconf',
                        help='backup configuration file')

    parser.add_argument('-p', '--pid-file', dest='pidfile',
                        default='/var/run/backup.pid',
                        help='where pid is writen to ')
    parser.add_argument('--version', '-v', action="store_true",
                        help="display version")
    parser.add_argument('-f', dest='foreground',
                        action="store_true",
                        help="run on foreground")
    parsed_args, extras = parser.parse_known_args(args)

    return parser, parsed_args, extras


def hdr(s):
    print '\n', s, '\n', '=' * len(s)


def do_basic_help(parser, args):
    """
    Print basic parser help
    """
    hdr('General usage:')
    parser.print_help()
    sys.exit(0)


from cherrypy._cpcompat import base64_decode

class Root(object):
    @cherrypy.expose
    def index(self, *args, **kwargs):
        return open(os.path.join(MYDIR, 'static/index.html'))

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def login(self,*args, **kwargs):
        request = cherrypy.serving.request
        return authentication.login(request, **kwargs)

def CORS():
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"


@cherrypy.expose()
class BackupPolicyService(object):
    def __init__(self, conf):
        self.conf = conf
        self.router = router.APIRouter(conf)

    @authentication.check_login
    def GET(self, *args, **kwargs):
        result = self.router.dispatch(cherrypy.request)
        return result

    @cherrypy.tools.json_out()
    @authentication.check_login
    def POST(self, *args, **kwargs):
        result = self.router.dispatch(cherrypy.request)
        return result

    @cherrypy.tools.json_out()
    @authentication.check_login
    def PUT(self, *args, **kwargs):
        result = self.router.dispatch(cherrypy.request)
        return result

    @cherrypy.tools.json_out()
    @authentication.check_login
    def DELETE(self, *args, **kwargs):
        result = self.router.dispatch(cherrypy.request)
        return result

    def OPTIONS(self, *arg, **kwargs):
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'PUT, DELETE'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'content-type, Access-Control-Allow-Headers, ' \
                                                                    'Authorization, X-Requested-With'
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'

conf = Config()

if __name__ == '__main__':
    os.chdir(MYDIR)
    parser, parsed_args, childargs = parse_cmdargs()
    if parsed_args.version:
        print('backup server version {0} '.format(BACKUP_VER))
        sys.exit(0)
    if parsed_args.help:
        do_basic_help(parser, childargs)
    config_path = 'server.conf'
    if parsed_args.backupconf:
        config_path = parsed_args.backupconf

    PIDFile(cherrypy.engine, parsed_args.pidfile).subscribe()
    if not parsed_args.foreground:
        Daemonizer(cherrypy.engine).subscribe()


    cherrypy.config.update({'log.screen': False,
                            'log.access_file': '',
                            'log.error_file': ''})


    cherrypy.config.update(errorpage.pages)
    cherrypy.engine.unsubscribe('graceful', cherrypy.log.reopen_files)
    cherrypy.config.update(config_path)
    conf.update(config_path)
    log.setup(conf)
    authentication.init(conf)
    root = Root()
    root.backup = BackupPolicyService(conf)
    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)
    cherrypy.tree.mount(root, '/', config_path)
    cherrypy.engine.start()
    cherrypy.engine.block()
