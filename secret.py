OP_RETURN_MAX_DATA = 40
POE_MARKER_BYTES = 'FOREVER '

# scriptPubkey is obtained from the following command in Bitcoin Core:
# validateaddress "1OneSendingAddressABCDEFG123456789"
# It is also possible to obtain it from:
# gettxout "abcdef0123456789abcdef9876543210fcabddeff258392cc83758dfbaa32d31" 2

PAYMENT_OBJ={'1oneSendingAddressABCDEFG123456789':['KprivateKeyCompressedUncompressedWhateverYouPreferHi', b'76a914cafebabe0123456789abcdeffedcba98765432102357'],
             '1AnotherSendingAddressGFEDCBA12389':['KAnotherPrivateKeyCompressedKeysAreBetterCUL8rByeBro', b'76a9144354565476587978893453535abcd342165eeffb3461']
             }

PUSH_TX_URL='https://insight.bitpay.com/api/tx/send'
#PUSH_TX_URL='http://127.0.0.1:8080/api/tx/send'