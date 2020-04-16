# -*- coding: utf-8 -*-

import flask
import hide.utils.Log as lg
from inspect import currentframe, getframeinfo
import json
import hide.utils.CmdLine as cl
import os
import re

#
# Flask is not multithreaded, all requests are lined up. This explains why request
# variables are global.
# To make it multithreaded, we declare this app application that already implements
# the method required by the WSGI (gunicorn)
#
app = flask.Flask(__name__)


#
# Flask DOES NOT run in multithreaded mode and handle 1 request at
# one time. Wrap it with gunicorn.
#
class HideApi:

    EXAMPLE_USAGE = \
        'http://localhost:5000/hide?'\
        +'ret=1&'\
        +'pattern=m,float,dollar/dollars/make/$;y,number,year/yr,2-4&'\
        +'txt=my salary in year 2019 is $8888.'

    def __init_rest_urls(self):
        #
        # Mex parameters extraction
        #
        @self.app.route('/mex', methods=['GET'])
        def gbot_api_get_mex_params():
            pattern = self.get_param(param_name='pattern', method='GET')
            text = self.get_param(param_name='txt', method='GET')
            ret_how_many = self.get_param(param_name='ret', method='GET')

            if not (pattern and text):
                return 'Missing parameters "pattern" or "txt". '\
                       + 'Example Usage: "' + HideApi.EXAMPLE_USAGE + '".'
            ret_one_value = True
            if ret_how_many == '2':
                ret_one_value = False
            return self.get_hide_params(
                pattern=pattern, text=text, return_one_value=ret_one_value
            )
        @self.app.errorhandler(404)
        def page_not_found(e):
            lg.Log.error(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                       + ': Resource [' + str(flask.request.url) + '] is not valid!')
            return "<h1>404</h1><p>The resource could not be found.</p>", 404

    def __init__(
            self
    ):
        self.app = app
        self.port = 5000
        self.app.config['DEBUG'] = False
        self.__init_rest_urls()
        return

    def hide_data(
            self,
            data
    ):
        try:
            pass
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                     + ' Exception occurred IP ' + str(flask.request.remote_addr) \
                     + ', data ' + str(data) \
                     + ', exception ' + str(ex) + '.'
            lg.Log.error(errmsg)
            if lg.Log.DEBUG_PRINT_ALL_TO_SCREEN:
                raise Exception(errmsg)
            return errmsg

    def get_param(self, param_name, method='GET'):
        if method == 'GET':
            if param_name in flask.request.args:
                return str(flask.request.args[param_name])
            else:
                return ''
        else:
            try:
                val = flask.request.json[param_name]
                return val
            except Exception as ex:
                lg.Log.critical(str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                           + ': No param name [' + param_name + '] in request.')
                return None

    def run_mex_api(self, host='0.0.0.0'):
        self.app.run(
            host = host,
            port = self.port,
            # threaded = True
        )


#
# Decide whether to run multi-threaded in gunicorn or not
#
pv = cl.CmdLine.get_cmdline_params(pv_default={'gunicorn': '0'})
mex_api = HideApi()
cwd = os.getcwd()
cwd = re.sub(pattern='([/\\\\]hide[/\\\\]).*', repl='/hide/', string=cwd)
lg.Log.LOGFILE = cwd + 'logs/hide.log'
print('Logs will be directed to log file (with date) "' + str(lg.Log.LOGFILE) + '"')
if pv['gunicorn'] == '1':
    lg.Log.important('Starting Mex API with gunicorn from folder "' + str(cwd))
    # Port and Host specified on command line already for gunicorn
else:
    lg.Log.important('Starting Mex API without gunicorn from folder "' + str(cwd))
    mex_api.run_mex_api()
