# -*- coding: utf-8 -*-

import re
from hide.utils.Log import Log
from inspect import getframeinfo, currentframe


class PhoneNumber:

    CHINA_COUNTRY_CODE = '86'

    @staticmethod
    def filter_phone_china(x):
        #
        # See https://en.wikipedia.org/wiki/Telephone_numbers_in_China
        # To call in China, the following format is used:
        #
        # For fixed phones:
        # xxx xxxx | xxxx xxxx Calls within the same area code
        #
        # 0yyy xxx xxxx (11 digits) | 0yyy xxxx xxxx (12 digits) Calls from other areas within China
        #
        # +86 yyy xxx xxxx (12 digits) | +86 yyy xxxx xxxx (13 digits) Calls from outside China
        #
        # For mobile phones:
        # 1nn xxxx xxxx (11 digits) Calls to mobile phones within China
        #
        # +86 1nn xxxx xxxx (13 digits) Calls to mobiles from outside China
        #
        try:
            str_number = re.sub(pattern='[^0-9]', repl='', string=str(x))
            # At least 10 digits
            len_no = len(str_number)
            if len_no < 10:
                return None

            if str_number[0] == '0':
                # Landline formats 0yyy xxx xxxx (11 digits) or 0yyy xxxx xxxx (12 digits)
                if len_no in [11, 12]:
                    return '+' + PhoneNumber.CHINA_COUNTRY_CODE + str_number[1:len_no]
            elif str_number[0] == '1':
                if len_no in [11]:
                    # Mobile number format 1nn xxxx xxxx (11 digits)
                    return '+' + PhoneNumber.CHINA_COUNTRY_CODE + str_number
            elif str_number[0:2] == PhoneNumber.CHINA_COUNTRY_CODE:
                # Landline formats +86 yyy xxx xxxx (12 digits) | +86 yyy xxxx xxxx (13 digits)
                # Mobile format 86 1nn xxxx xxxx (13 digits)
                if len_no in [12, 13]:
                    return '+' + str_number
            else:
                # Landline formats yyy xxx xxxx (10 digits) | yyy xxxx xxxx (11 digits)
                if len_no in [10, 11]:
                    return '+' + PhoneNumber.CHINA_COUNTRY_CODE + str_number
                else:
                    # TODO Should we just return whatever we have then? Instead of throwing exception.
                    pass

            raise Exception('Invalid ' + str(len_no) + ' digit phone number ' + str(str_number) + '')
        except Exception as ex:
            Log.error(
                str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Error phone number: ' + str(ex)
            )
            return None

    def __init__(self):
        return