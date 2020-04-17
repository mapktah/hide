# -*- coding: utf-8 -*-

import requests
import json

hide_url = 'http://localhost:5088/hide'
datetime_format = '%Y-%m-%d %H:%M:%S'

#
# Pull Feed
#
data = {
    'records': [{"MemberKey":"jinping","Name":"习近平"},{"MemberKey":"jinping2","Name":"%20习近平"}],
    'hide_colname': "Name",
    'encrypt_key_b64': 'U2l4dGVlbiBieXRlIGtleVNpeHRlZW4gYnl0ZSBrZXk='
}

restResponse = requests.post(
    url     = hide_url,
    json    = data,
    # No need to verify HTTPS
    verify  = False,
    timeout = 1.0
)
if restResponse.ok:
    print('Server response OK.')
    print(restResponse.text)
    data = json.loads(restResponse.content)
    print(type(data))
    for i in range(len(data)):
        print(str(i) + '. ' + str(data[i]))

