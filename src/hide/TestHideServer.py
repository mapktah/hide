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
for i in range(10):
    load_test_records.append({
        'MemberKey': ''.join(random.choice(CHARS_ASCII + CHARS_NUMBER) for j in range(randint(6,10))),
        'Name': ''.join(chr(randint(BLOCK_CHINESE[0], BLOCK_CHINESE[1])) for k in range(randint(3,5))),
        'Phone': '+86'  + ''.join(random.choice(CHARS_NUMBER) for l in range(11))
    })
len_records = len(load_test_records)

print(load_test_records)

#
# Pull Feed
#
data = {
    'records': load_test_records,
    #'col_to_hide': "Name",
    'col_to_hide': "Phone",
    #'process_phone_country': None,
    'process_phone_country': 'china',
    'is_number_only': 1,
    'encrypt_key_b64': 'U2l4dGVlbiBieXRlIGtleVNpeHRlZW4gYnl0ZSBrZXk='
}

starttime = datetime.now()

restResponse = requests.post(
    url     = hide_url,
    json    = data,
    # No need to verify HTTPS
    verify  = False,
    timeout = 60.0
)
if restResponse.ok:
    print('Server response OK.')
    print(restResponse.text)
    data = json.loads(restResponse.content)
    print(type(data))
    for i in range(len(data)):
        print(str(i) + '. ' + str(data[i]))

endtime = datetime.now()
difftime = endtime - starttime
diffsecs = round(difftime.days * 86400 + difftime.seconds + difftime.microseconds/1000000, 2)
print(
    str(len_records) + ' records took ' + str(diffsecs) + ' secs'
    + ', or ' + str(round(1000*diffsecs/len_records, 2)) + ' ms per record'
)