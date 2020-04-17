# -*- coding: utf-8 -*-

from hide.utils.Log import Log
from inspect import currentframe, getframeinfo
import json
import re
import pandas as pd
from hide.utils.StringUtils import StringUtils
from hide.utils.Hash import Hash
from hide.utils.Encrypt import AES_Encrypt
from hide.utils.PhoneNumber import PhoneNumber
from base64 import b64decode
from hide.utils.Profiling import Profiling


class Hide:

    def __init__(self):
        return

    def hide_data(
            self,
            # In string JSON
            records_json,
            # Column names to hide
            hide_colname,
            encrypt_key_b64,
            nonce_b64        = None,
            is_number_only   = False,
            case_sensitive   = False,
            # We support processing only China for now
            process_phone_country = None,
            hash_encode_lang = 'zh',
    ):
        step = 0

        if type(records_json) is str:
            try:
                records_json = json.loads(
                    records_json
                )
            except Exception as ex_json:
                errmsg = \
                    str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno) \
                    + ': Exception loading json: ' + str(records_json)\
                    + '. Got exception: ' + str(ex_json)
                Log.error(errmsg)
                return errmsg

        colname_clean            = str(hide_colname) + '_clean'
        colname_last4char        = str(hide_colname) + '_last4char'
        colname_hash             = str(hide_colname) + '_sha256'
        colname_hash_readable    = str(hide_colname) + '_sha256_readable'
        colname_encrypt          = str(hide_colname) + '_encrypt'
        colname_encrypt_readable = str(hide_colname) + '_encrypt_readable'

        df = pd.DataFrame(records_json)
        Log.debug(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Converted json object (first 20 records): '
            + str(records_json[0:min(20,len(records_json))])
            + ' to data frame: ' + str(df)
        )

        Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Start processing records, hide column "' + str(hide_colname)
            + '". Records of sample rows' +  str(records_json[0:min(10,len(records_json))])
        )

        #
        # Step 1
        #  - Clean phone numbers, bank accounts
        #  - Extract last 4 digits of phone/bank-account numbers to separate columns
        #  - Obfuscate the phone numbers, bank accounts for storage in cube
        #
        step += 1
        start_filter_time = Profiling.start()
        def filter_col(
                x,
                is_number_only = False,
                case_sensitive = False
        ):
            try:
                # We always trim no matter what
                x = StringUtils.trim(str(x))
                if not case_sensitive:
                    x = x.lower()
                if is_number_only:
                    x = re.sub(pattern='[^0-9]', repl='', string=x)
                return x
            except Exception:
                return None
        df[colname_clean] = df[hide_colname].apply(filter_col, args=(is_number_only, case_sensitive))
        Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Step ' + str(step) + ': BASIC CLEANING Took '
            + str(Profiling.get_time_dif_secs(start=start_filter_time, stop=Profiling.stop(), decimals=2))
            + ' secs. Successfully cleaned column "' + str(hide_colname)+
            '", case sensitive "' + str(case_sensitive)
            + '", is number "' + str(is_number_only)
            + '", sample rows: ' + str(df[0:2])
        )

        #
        # Process Phone Number by Country
        #
        step += 2
        start_phone_time = Profiling.start()
        def process_phone(
                x,
                country
        ):
            try:
                if country == 'china':
                    return PhoneNumber.filter_phone_china(x)
                else:
                    Log.error(
                        str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                        + ': Unsupported country "' + str(country) + '"'
                    )
                    return x
            except Exception as ex:
                Log.error(
                    str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                    + ': Exception processing phone "' + str(x) + '". Exception ' + str(ex)
                )
                return x

        if process_phone_country == 'china':
            df[colname_clean] = df[colname_clean].apply(process_phone, args=[process_phone_country])
            Log.important(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Step ' + str(step) + ': PHONE CLEANING Took '
                + str(Profiling.get_time_dif_secs(start=start_phone_time, stop=Profiling.stop(), decimals=2))
                + ' secs. Successfully processed phone for column "' + str(hide_colname)
                + '", sample rows: ' + str(df[0:2])
            )

        #
        # Extract last 4 characters
        #
        step += 1
        start_last4_time = Profiling.start()
        def last4char(
                x
        ):
            len_x = len(str(x))
            start = max(0, len_x - 4)
            return '***' + str(x)[start:len_x]
        df[colname_last4char] = df[colname_clean].apply(last4char)
        Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Step ' + str(step) + ': EXTRACT LAST 4 CHAR Took '
            + str(Profiling.get_time_dif_secs(start=start_last4_time, stop=Profiling.stop(), decimals=2))
            + ' secs. Successfully extracted last 4 chars from column "' + str(hide_colname)
            + '"'
        )

        #
        # Hash the column
        #
        step += 1
        start_hash_time = Profiling.start()
        def hash(
                x,
                desired_byte_len = 32
        ):
            s = Hash.hash(
                string = x,
                algo   = Hash.ALGO_SHA256
            )
            # obf = Obfuscate()
            # bytes_list = obf.hash_compression(
            #     s                   = str(x),
            #     desired_byte_length = desired_byte_len
            # )
            # s = obf.hexdigest(
            #     bytes_list    = bytes_list,
            #     unicode_range = None
            # )
            return s

        df[colname_hash] = df[colname_clean].apply(hash, args=[32])
        stop_hash_time = Profiling.start()
        Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Step ' + str(step) + ': HASH Took '
            + str(Profiling.get_time_dif_secs(start=start_hash_time, stop=stop_hash_time, decimals=2))
            + ' secs. Successfully obfuscated column "' + str(hide_colname)
            + '", sample rows: ' + str(df[0:2])
        )

        #
        # Obfuscate Hash hexdigest to Chinese/etc characters
        #
        step += 1
        start_obflang_time = Profiling.start()
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

        df[colname_hash_readable] = df[colname_hash].apply(obfuscate_hash_to_lang, args=[hash_encode_lang])
        Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Step ' + str(step) + ': HASH TO CHAR Took '
            + str(Profiling.get_time_dif_secs(start=start_obflang_time, stop=Profiling.stop(), decimals=2))
            + ' secs. Successfully converted obfuscation to language for column "' + str(hide_colname)
            + '"'
        )

        #
        # Ecnryption
        #
        step += 1
        start_enc_time = Profiling.start()
        try:
            key_bytes = b64decode(encrypt_key_b64.encode('utf-8'))
        except Exception as ex_key_conversion:
            raise Exception(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Error converting base64 key "' + str(encrypt_key_b64)
                + '" to bytes. Exception: ' + str(ex_key_conversion)
            )
        try:
            nonce_bytes = b64decode(nonce_b64.encode(encoding='utf-8'))
        except Exception as ex_nonce:
            Log.warning(
                str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
                + ': Error converting base64 nonce "' + str(nonce_b64)
                + '" to bytes. Exception: ' + str(ex_nonce)
            )
            nonce_bytes = None
        Log.important(
            str(__name__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Step ' + str(step) + ': HASH Took '
            + ': Key bytes "' + str(key_bytes) + '", len = ' + str(len(key_bytes))
        )
        encryptor = AES_Encrypt(
            key   = key_bytes,
            mode  = AES_Encrypt.AES_MODE_CBC,
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
                ciphermode = res.cipher_mode
                ciphertext_b64 = res.ciphertext_b64
                tag_b64 = res.tag_b64
                nonce_b64 = res.nonce_b64
                # print('***** cipher=' + str(cipher) + ', bytelen=' + str(len(cipher)))
                # plaintext = encryptor.decode(ciphertext=ciphertext_b64)
                # print('***** decrypted=' + str(plaintext) + ', ok=' + str(plaintext==x))
                # if plaintext != x:
                #     raise Exception('Decrypt Failed for x "' + str(x) + '", decypted "' + str(plaintext) + '"')
                return {
                    'ciphermode': ciphermode,
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
        Log.important(
            str(self.__class__) + ' ' + str(getframeinfo(currentframe()).lineno)
            + ': Took ' + str(Profiling.get_time_dif_secs(start=start_enc_time, stop=Profiling.stop(), decimals=2))
            + ' secs. Successfully encrypted column "' + str(hide_colname)
            + '", for records (first 20 rows): ' + str(df.values[0:min(20,df.shape[0])])
        )

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
    print('JSON string: ' + str(json_str))

    for col_instruction in [
        ('Name', False, False), ('Phone', True, False), ('Email', False, False), ('BankAcc', True, False)
    ]:
        res = Hide().hide_data(
            records_json     = json_str,
            hide_colname     = col_instruction[0],
            is_number_only   = col_instruction[1],
            case_sensitive   = col_instruction[2],
            encrypt_key_b64  = 'U2l4dGVlbiBieXRlIGtleVNpeHRlZW4gYnl0ZSBrZXk='
        )
        print(res)

    exit(0)
