import json, urllib, datetime, io, binascii
from google.appengine.api import urlfetch
from pycoin.tx.script import tools
from pycoin.encoding import wif_to_secret_exponent
from pycoin.tx.pay_to import build_hash160_lookup
from pycoin.tx import Spendable, TxIn, TxOut, Tx
from model import ErrorNotification
from secret import POE_MARKER_BYTES, OP_RETURN_MAX_DATA, PUSH_TX_URL, PAYMENT_OBJ
import test

def spendables_for_address(_from, unused_utxo): # Generate spendables without connecting to the Bitcoin network
    spendables = []
    
    _script_p2pkh=PAYMENT_OBJ[_from][1]
    coin_value = unused_utxo.satoshis
    script = binascii.unhexlify(_script_p2pkh)  
    
    previous_hash_big_endian = binascii.unhexlify(unused_utxo.txid)
    previous_hash_little_endian = previous_hash_big_endian[::-1]
    
    previous_index = unused_utxo.vout
    
    return [Spendable(coin_value, script, previous_hash_little_endian, previous_index)]

def construct_data_tx(data, _from, unused_utxo):
  
  coins_from = spendables_for_address(_from, unused_utxo) #Ahora
  
  if len(coins_from) < 1:
    ErrorNotification.new('No bitcoins available to spend')  
    return 'No bitcoins available to spend'
  
  txs_in = [TxIn(coins_from[0].tx_hash, coins_from[0].tx_out_index, coins_from[0].script)] 
  script_text = 'OP_RETURN %s' % data.encode('hex')

  script_bin = tools.compile(script_text)
  
  new_txs_out = [TxOut(0, script_bin)]
  version = 1
  lock_time = 0
  unsigned_tx = Tx(version, txs_in, new_txs_out, lock_time, coins_from)

  return unsigned_tx
 

def tx2hex(tx):
  s = io.BytesIO()
  tx.stream(s)
  tx_bytes = s.getvalue()
  tx_hex = binascii.hexlify(tx_bytes).decode('utf8')
  return tx_hex


def pushtxn(raw_tx):
  '''Insight send raw tx API''' 
  url = PUSH_TX_URL
  payload = urllib.urlencode({
    "rawtx": raw_tx 
  })
  result = urlfetch.fetch(url,
    method=urlfetch.POST,
    payload=payload
  )
  
  if result.status_code == 200:  
    j = json.loads(result.content)
    txid = j.get('txid')
    return txid, raw_tx
  else: 
    msg = 'Error accessing insight API:'+str(result.status_code)+" "+str(result.content)
    ErrorNotification.new(msg) 
    return None, msg

def publish_data(data, unused_utxo):
  data = POE_MARKER_BYTES + data
  if len(data) > OP_RETURN_MAX_DATA:
    msg='data too long for OP_RETURN: %s' % (data.encode('hex'))
    ErrorNotification.new(msg)  
    return None, msg

  _from = unused_utxo.address
  _private_key=PAYMENT_OBJ[_from][0]
  secret_exponent = wif_to_secret_exponent(_private_key) #mainnet
  
  unsigned_tx = construct_data_tx(data, _from, unused_utxo)
  
  if type(unsigned_tx) == str: # error
    msg='ERROR: type(unsigned_tx) == str'
    ErrorNotification.new(msg) 
    return (None, unsigned_tx)

  solver = build_hash160_lookup([secret_exponent])  
  signed_tx = unsigned_tx.sign(solver) 
  raw_tx = tx2hex(signed_tx)
  
  txid, message = pushtxn(raw_tx)
  return txid, message
