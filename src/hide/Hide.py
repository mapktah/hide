# -*- coding: utf-8 -*-

from hide.utils.Log import Log
from inspect import currentframe, getframeinfo
import json
import re
import pandas as pd
from hide.utils.StringUtils import StringUtils
from hide.utils.Hash import Hash
from hide.utils.Obfuscate import Obfuscate
from hide.utils.Encrypt import AES_Encrypt, AES


class Hide:

    COL_MBR_KEY     = 'MemberKey'
    COL_MBR_NAME    = 'Name'
    COL_MBR_PHONE   = 'Phone'
    COL_MBR_EMAIL   = 'Email'
    COL_MBR_BANKACC = 'BankAcc'

    # Feature columns
    COL_NAME_HASH    = '__name_hash'
    COL_PHONE_HASH   = '__phone_hash'
    COL_EMAIL_HASH   = '__email_hash'
    COL_BANKACC_HASH = '__bank_acc_hash'
    FEATURE_COLUMNS = [
        COL_NAME_HASH, COL_PHONE_HASH, COL_EMAIL_HASH, COL_BANKACC_HASH
    ]

    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
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
            records_json = json.loads(
                records_json_str
            )
        except Exception as ex_json:
            errmsg = \
                str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                + ': Exception loading json: ' + str(ex_json)
            Log.error(errmsg)
            return errmsg

        colname_clean            = str(hide_colname) + '_clean'
        colname_last4char        = str(hide_colname) + '_last4char'
        colname_hash             = str(hide_colname) + '_hash'
        colname_hash_readable    = str(hide_colname) + '_hash_readable'
        colname_encrypt          = str(hide_colname) + '_encrypt'
        colname_encrypt_readable = str(hide_colname) + '_encrypt_readable'

        df = pd.DataFrame(records_json)
        Log.debug(
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Converted json str: ' + str(records_json_str)
            + ' to data frame: ' + str(df)
        )

        #
        # Step 1
        #  - Clean phone numbers, bank accounts
        #  - Extract last 4 digits of phone/bank-account numbers to separate columns
        #  - Obfuscate the phone numbers, bank accounts for storage in cube
        #
        def filter_col(
                x,
                is_number_only = False,
                case_sensitive = False
        ):
            try:
                if not case_sensitive:
                    x = StringUtils.trim(str(x).lower())
                if is_number_only:
                    x = re.sub(pattern='[^0-9]', repl='', string=str(x))
                return x
            except Exception:
                return None
        df[colname_clean] = df[hide_colname].apply(filter_col, args=(is_number_only, case_sensitive))

        def last4char(
                x
        ):
            len_x = len(str(x))
            start = max(0, len_x - 4)
            return '***' + str(x)[start:len_x]
        df[colname_last4char] = df[colname_clean].apply(last4char)

        def obfuscate(
                x,
                desired_byte_len = 32
        ):
            obf = Obfuscate()
            bytes_list = obf.hash_compression(
                s                   = str(x),
                desired_byte_length = desired_byte_len
            )
            s = obf.hexdigest(
                bytes_list    = bytes_list,
                unicode_range = None
            )
            return s[2:len(s)]

        df[colname_hash] = df[colname_clean].apply(obfuscate, args=[32])

        def obfuscate_hash_to_lang(
                x,
                lang
        ):
            unicode_range = Hash.BLOCK_CHINESE
            if lang == 'ko':
                unicode_range = Hash.BLOCK_KOREAN_SYL
            s = Hash.convert_hash_to_char(
                hash_hex_string = x,
                unicode_range   = unicode_range
            )
            return s
            #return s[2:len(s)]

        df[colname_hash_readable] = df[colname_hash].apply(obfuscate_hash_to_lang, args=[hash_encode_lang])

        key_bytes = bytes(encrypt_key_str.encode('utf-8'))
        Log.important(
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Key bytes "' + str(key_bytes) + '", len = ' + str(len(key_bytes))
        )
        encryptor = AES_Encrypt(
            key   = key_bytes,
            mode  = AES.MODE_CBC,
        )
        def encrypt(
                x,
                encryptor
        ):
            try:
                # print('***** x=' + str(x))
                x_bytes = bytes(x.encode(encoding='utf-8'))
                # print('***** x_bytes=' + str(x_bytes))
                cipher = encryptor.encode(x_bytes)
                ciphertext = str(cipher)
                print('***** cipher=' + str(cipher) + ', bytelen=' + str(len(cipher)))
                # plaintext = encryptor.decode(ciphertext=cipher)
                # print('***** decrypted=' + str(plaintext) + ', ok=' + str(plaintext==x))
                # if plaintext != x:
                #     raise Exception('Decrypt Failed for x "' + str(x) + '", decypted "' + str(plaintext) + '"')
                return ciphertext
            except Exception as ex:
                Log.error(
                    str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Error encrypting "' + str(x) + '": ' + str(ex)
                )
                return None

        df[colname_encrypt] = df[colname_clean].apply(encrypt, args=[encryptor])

        def obfuscate_cipher_to_lang(
                x,
                lang
        ):
            x_bytes = bytes(x.encode(encoding='utf-8'))
            print('*** x=' + str(x))
            print('*** xbytes=' + str(x_bytes))
            unicode_range = Hash.BLOCK_CHINESE
            if lang == 'ko':
                unicode_range = Hash.BLOCK_KOREAN_SYL
            s = Hash.convert_hash_to_char(
                hash_hex_string = x,
                unicode_range   = unicode_range
            )
            return s[2:len(s)]

        # df[colname_encrypt_readable] = df[colname_encrypt].apply(obfuscate_cipher_to_lang, args=[hash_encode_lang])

        df_json_str = df.to_json(
            # Make sure not ASCII
            force_ascii = False,
            orient      = 'records',
            # Don't need indexing
            # index       = False
        )

        return df_json_str


if __name__ == '__main__':
    Log.LOGLEVEL = Log.LOG_LEVEL_DEBUG_1

    sample_string = '\
[{"MemberKey":"jinping","Name":" 习近平","Phone":" +86 711-1246-0114","Email":" jinping@qq.com","BankAcc":" 00-777-88"},\
{"MemberKey":"jinping2","Name":" 习近平","Phone":" 07111246-0114","Email":" jinping@qq.com","BankAcc":" 00-777-88"}]\
    '
    #print(sample_string)

    sample_data_path = 'sampledata.csv'
    df = pd.read_csv(sample_data_path)
    #print(df)
    json_str = df.to_json(
        # Make sure not ASCII
        force_ascii = False,
        orient      = 'records',
        # Don't need indexing
        # index       = False
    )
    #print(json_str)

    for col_instruction in [
        ('Name', False, False), ('Phone', True, False), ('Email', False, False), ('BankAcc', True, False)
    ]:
        res = Hide().hide_data(
            records_json_str = json_str,
            hide_colname     = col_instruction[0],
            is_number_only   = col_instruction[1],
            case_sensitive   = col_instruction[2],
            encrypt_key_str  = 'Sixteen byte key'+'Sixteen byte key'
        )
        print(res)

    exit(0)
