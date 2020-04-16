# -*- coding: utf-8 -*-

import flask
from flask import request
import hide.utils.Log as lg
from inspect import currentframe, getframeinfo
import hide.utils.CmdLine as cl
import os
import re
from hide.Hide import Hide


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

    # http://localhost:5000/hide?records=[{"MemberKey":"jinping","Name":"习近平"},{"MemberKey":"jinping2","Name":"%20习近平"}]&hide_colname=Name&is_number_only=0&case_sensitive=0&encrypt_key_str=xxxxxxxyyyyyzzzz
    EXAMPLE_USAGE = \
        'http://localhost:5000/hide?'\
        +'records=[{"MemberKey":"jinping","Name":"习近平"},{"MemberKey":"jinping2","Name":" 习近平"}]'\
        +'&hide_colname=Name&is_number_only=0&case_sensitive=0&encrypt_key_str=xxxxxxxyyyyyzzzz'

    def __init_rest_urls(self):
        #
        # Mex parameters extraction
        #
        @self.app.route('/hide', methods=['GET', 'POST'])
        def api_hide():
            method = request.method
            records_json_str = self.get_param(param_name='records', method=method)
            hide_colname = self.get_param(param_name='hide_colname', method=method)
            is_number_only = self.get_param(param_name='is_number_only', method=method)
            case_sensitive = self.get_param(param_name='case_sensitive', method=method)
            encrypt_key_str = self.get_param(param_name='encrypt_key_str', method=method)
            return self.hide_data(
                records_json_str = records_json_str,
                hide_colname     = hide_colname,
                is_number_only   = is_number_only,
                case_sensitive   = case_sensitive,
                encrypt_key_str  = encrypt_key_str,
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
            # In string JSON
            records_json_str,
            # Column names to hide
            hide_colname,
            encrypt_key_str,
            is_number_only   = False,
            case_sensitive   = False,
            hash_encode_lang = 'zh',
    ):
        try:
            return Hide().hide_data(
                records_json_str = records_json_str,
                hide_colname     = hide_colname,
                is_number_only   = (is_number_only in [1, '1', 'y', 'yes']),
                case_sensitive   = (case_sensitive in [1, '1', 'y', 'yes']),
                encrypt_key_str  = encrypt_key_str
            )
        except Exception as ex:
            errmsg = str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                     + ' Exception occurred IP ' + str(flask.request.remote_addr) \
                     + ', records ' + str(records_json_str) \
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

    def run_hide_api(self, host='0.0.0.0'):
        self.app.run(
            host = host,
            port = self.port,
            # threaded = True
        )


#
# Decide whether to run multi-threaded in gunicorn or not
#
pv = cl.CmdLine.get_cmdline_params(pv_default={'gunicorn': '0'})
rest_api = HideApi()
cwd = os.getcwd()
cwd = re.sub(pattern='([/\\\\]hide[/\\\\]).*', repl='/hide/', string=cwd)
lg.Log.LOGFILE = cwd + 'logs/hide.log'
print('Logs will be directed to log file (with date) "' + str(lg.Log.LOGFILE) + '"')
if pv['gunicorn'] == '1':
    lg.Log.important('Starting Mex API with gunicorn from folder "' + str(cwd))
    # Port and Host specified on command line already for gunicorn
else:
    lg.Log.important('Starting Mex API without gunicorn from folder "' + str(cwd))
    rest_api.run_hide_api()
