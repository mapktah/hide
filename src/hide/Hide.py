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
from base64 import b64decode


class Hide:

    def __init__(self):
        return

    def hide_data(
            self,
            # In string JSON
            records_json_str,
            # Column names to hide
            hide_colname,
            encrypt_key_b64,
            nonce_b64        = None,
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
                + ': Exception loading json: ' + str(records_json_str)\
                + '. Got exception: ' + str(ex_json)
            Log.error(errmsg)
            return errmsg

        colname_clean            = str(hide_colname) + '_clean'
        colname_last4char        = str(hide_colname) + '_last4char'
        colname_hash             = str(hide_colname) + '_hash'
        colname_hash_readable    = str(hide_colname) + '_hash_readable'
        colname_encrypt          = str(hide_colname) + '_encrypt_b64'
        colname_encrypt_readable = str(hide_colname) + '_encrypt_b64_readable'

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
            s = Hash.convert_ascii_string_to_other_alphabet(
                ascii_char_string = x,
                unicode_range     = unicode_range,
                group_n_char      = 4
            )
            return s
            #return s[2:len(s)]

        df[colname_hash_readable] = df[colname_hash].apply(obfuscate_hash_to_lang, args=[hash_encode_lang])

        key_bytes = b64decode(encrypt_key_b64.encode('utf-8'))
        if nonce_b64 is not None:
            nonce_bytes = b64decode(nonce_b64.encode(encoding='utf-8'))
        else:
            nonce_bytes = None
        Log.important(
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Key bytes "' + str(key_bytes) + '", len = ' + str(len(key_bytes))
        )
        encryptor = AES_Encrypt(
            key   = key_bytes,
            mode  = AES.MODE_CBC,
            nonce = nonce_bytes
        )
        def encrypt(
                x,
                encryptor
        ):
            try:
                # print('***** x=' + str(x))
                x_bytes = bytes(x.encode(encoding='utf-8'))
                # print('***** x_bytes=' + str(x_bytes))
                res = encryptor.encode(x_bytes)
                ciphertext_b64 = res.ciphertext_b64
                tag_b64 = res.tag_b64
                nonce_b64 = res.nonce_b64
                # print('***** cipher=' + str(cipher) + ', bytelen=' + str(len(cipher)))
                plaintext = encryptor.decode(ciphertext=ciphertext_b64)
                #print('***** decrypted=' + str(plaintext) + ', ok=' + str(plaintext==x))
                if plaintext != x:
                    raise Exception('Decrypt Failed for x "' + str(x) + '", decypted "' + str(plaintext) + '"')
                return {
                    'ciphertext_b64': ciphertext_b64,
                    'tag_b64': tag_b64,
                    'nonce_b64': nonce_b64
                }
            except Exception as ex:
                Log.error(
                    str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Error encrypting "' + str(x) + '": ' + str(ex)
                )
                return None

        df[colname_encrypt] = df[colname_clean].apply(encrypt, args=[encryptor])

        # def obfuscate_cipher_to_lang(
        #         x,
        #         lang
        # ):
        #     unicode_range = Hash.BLOCK_CHINESE
        #     if lang == 'ko':
        #         unicode_range = Hash.BLOCK_KOREAN_SYL
        #     s = Hash.convert_ascii_string_to_other_alphabet(
        #         ascii_char_string = x['ciphertext_b64'],
        #         unicode_range     = unicode_range,
        #         group_n_char      = 2
        #     )
        #     return s
        #
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
    print(json_str)

    for col_instruction in [
        ('Name', False, False), ('Phone', True, False), ('Email', False, False), ('BankAcc', True, False)
    ]:
        res = Hide().hide_data(
            records_json_str = json_str,
            hide_colname     = col_instruction[0],
            is_number_only   = col_instruction[1],
            case_sensitive   = col_instruction[2],
            encrypt_key_b64  = 'U2l4dGVlbiBieXRlIGtleVNpeHRlZW4gYnl0ZSBrZXk='
        )
        print(res)

    exit(0)
