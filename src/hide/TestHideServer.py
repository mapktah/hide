# -*- coding: utf-8 -*-

import requests
import json
import random
from random import randint
from datetime import datetime, timedelta

hide_url = 'http://localhost:5088/hide'
datetime_format = '%Y-%m-%d %H:%M:%S'

BLOCK_CHINESE = (0x4e00, 0x9fff)  # CJK Unified Ideographs
RANGE_CHINESE = BLOCK_CHINESE[1] - BLOCK_CHINESE[0] + 1
CHARS_ASCII = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
CHARS_THAI = 'ๅ/_ภถุึคตจขชๆไำพะัีรนยฟหกดเ้่าสผปแอิืท+๑๒๓๔ู฿๕๖๗๘๙๐ฎฑธ'
CHARS_NUMBER = '1234567890'
CHARS_SPECIAL = '`~!@#$%^&*()_+-=[]\{}|[]\\;\':",./<>?'

#
# Create random data
#
load_test_records = []
for i in range(50000):
    load_test_records.append({
        'MemberKey': ''.join(random.choice(CHARS_ASCII + CHARS_NUMBER) for j in range(randint(6,10))),
        'Name': ''.join(chr(randint(BLOCK_CHINESE[0], BLOCK_CHINESE[1])) for k in range(randint(3,5))),
        'Phone': '+86'  + ''.join(random.choice(CHARS_NUMBER) for l in range(11)),
        'Email': ''.join(random.choice(CHARS_ASCII) for m in range(randint(6,10))) + '@qq.com',
        'Acc': ''.join(random.choice(CHARS_NUMBER) for n in range(randint(4,6))) + '-'
               + ''.join(random.choice(CHARS_NUMBER) for p in range(randint(4,6))),
        'Password': ''.join(random.choice(CHARS_ASCII + CHARS_NUMBER) for q in range(randint(8, 10))),
    })
len_records = len(load_test_records)

#
# Pull Feed
#
json_hide_name = {
    'records': load_test_records,
    'col_to_hide': "Name",
    'process_phone_country': None,
    'is_number_only': 0,
    'case_sensitive': 0,
    'encrypt_key_b64': 'U2l4dGVlbiBieXRlIGtleVNpeHRlZW4gYnl0ZSBrZXk='
}
json_hide_phone = {
    'records': load_test_records,
    'col_to_hide': "Phone",
    'process_phone_country': 'china',
    'is_number_only': 1,
    'case_sensitive': 0,
    'encrypt_key_b64': 'U2l4dGVlbiBieXRlIGtleVNpeHRlZW4gYnl0ZSBrZXk='
}
json_hide_email = {
    'records': load_test_records,
    'col_to_hide': "Email",
    'process_phone_country': None,
    'is_number_only': 0,
    'case_sensitive': 0,
    'encrypt_key_b64': 'U2l4dGVlbiBieXRlIGtleVNpeHRlZW4gYnl0ZSBrZXk='
}
json_hide_acc = {
    'records': load_test_records,
    'col_to_hide': "Acc",
    'process_phone_country': None,
    'is_number_only': 1,
    'case_sensitive': 0,
    'encrypt_key_b64': 'U2l4dGVlbiBieXRlIGtleVNpeHRlZW4gYnl0ZSBrZXk='
}
json_hide_pwd = {
    'records': load_test_records,
    'col_to_hide': "Password",
    'process_phone_country': None,
    'is_number_only': 0,
    'case_sensitive': 1,
    'encrypt_key_b64': 'U2l4dGVlbiBieXRlIGtleVNpeHRlZW4gYnl0ZSBrZXk='
}

for json_data in [json_hide_name, json_hide_phone, json_hide_email, json_hide_acc, json_hide_pwd]:
    starttime = datetime.now()
    restResponse = requests.post(
        url     = hide_url,
        json    = json_data,
        # No need to verify HTTPS
        verify  = False,
        timeout = 60.0
    )
    if restResponse.ok:
        print('Server response OK.')
        # print(restResponse.text)
        data = json.loads(restResponse.content)
        print(type(data))
        for i in range(len(data)):
            if i>10:
                break
            print(str(i) + '. ' + str(data[i]))

    endtime = datetime.now()
    difftime = endtime - starttime
    diffsecs = round(difftime.days * 86400 + difftime.seconds + difftime.microseconds/1000000, 2)
    print(
        'Process col "' + str(json_data['col_to_hide'])
        + '" of ' + str(len_records) + ' records took ' + str(diffsecs) + ' secs'
        + ', or ' + str(round(1000*diffsecs/len_records, 2)) + ' ms per record'
    )