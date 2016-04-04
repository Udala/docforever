import webapp2, datetime, json, string, binascii, traceback
from google.appengine.ext import db
from model import Utxo, DocLine, DocRoot, ErrorNotification
from blockchain import publish_data
from merkle.merkle import MerkleError, Node, MerkleTree
from google.appengine.api.memcache import flush_all
from google.appengine.ext import ndb
from google.appengine.ext.ndb import Key
import test

# Tests 
class TestHandler(webapp2.RequestHandler):
    def get(self):
        self.post()
    
    def post(self):
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write('{"txid":"abcdef0123456789"}')


class CheckContentHandler(webapp2.RequestHandler):
    def get(self):
        status={"success": False, "reason":"Unknown reason"}
        
        contentHash = self.request.get("hash")
        hex_digits=set(string.hexdigits)
        
        if not contentHash or len(contentHash)!=64 or not all(c in hex_digits for c in contentHash):
            status = {"success" : False, "reason" : "content hash format"}
        else:
            old_doc=DocLine.get_doc(contentHash)
            if old_doc:
                if old_doc.doc_root:
                    doc_root=DocRoot.get_doc(old_doc.doc_root)
                    if doc_root:
                        status={"success":True, "stat":2, "txid": doc_root.txid, "merkle": eval(old_doc.merkle_chain)}
                    else:
                        ErrorNotification.new('Fatal: No merkle root for broadcast document')
                        status={"success":False, "reason": "Fatal: No merkle root for broadcast document" }
                else:
                    status={"success":True, "stat":1, "date": old_doc.date_received.strftime("%Y-%m-%d %H:%M:%S")}
            else:
                utcnow=test.utcnow()
                key_name_today=utcnow.strftime("%Y-%m-%d")+'/00'
                
                k=ndb.Key('DocRoot', key_name_today)
                today_doc_root=k.get()
                if today_doc_root:
                    DocLine.new(k, contentHash, utcnow)
                    status={"success":True, "stat":0, "date": utcnow.strftime("%Y-%m-%d %H:%M:%S")}
                else:
                    ErrorNotification.new('Fatal: DocRoot template for today not found!')
                    status={"success":False, "reason": "Fatal: DocRoot template for today not found!"}
        
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(json.dumps(status))
        
     
class BroadcastDailyHandler(webapp2.RequestHandler):
    
    @ndb.transactional
    def get_merkle_chains(self, root_key_name_yesterday):
        k=ndb.Key('DocRoot', root_key_name_yesterday)
        doc_root=k.get()
        
        if (doc_root.doc_root_hash!=''):
            raise Exception('ERROR! doc_root_hash already used!')
        
        my_list=DocLine.get_doclines_from_root(root_key_name_yesterday)
        
        if len(my_list)==0:
            raise Exception('WARNING. No documents to proof.')
        
        my_list2=map(lambda x:x.content_hash,my_list)
 
        tree = MerkleTree(my_list2, True)
        tree.build()
         
        doc_root_hash=binascii.hexlify(tree.root.val)
         
        for i in range(len(my_list2)):
            merkle_chain=tree.get_chain(i)
            merkle_chain2=map(lambda x: (binascii.hexlify(x[0]),x[1]), merkle_chain)
             
            my_list[i].merkle_chain=db.Text(str(merkle_chain2), encoding="latin-1")
            my_list[i].doc_root=doc_root_hash
            my_list[i].put()
             
        doc_root=k.get()
        
        doc_root.doc_root_hash=doc_root_hash
        doc_root.date_broadcast=test.utcnow()
        doc_root.nodes=db.Text(str(map(lambda x: binascii.hexlify(x.val), tree.leaves)), encoding='latin-1')
        doc_root.put()
        return doc_root_hash
        
    def publish_raw_tx(self, key_name, doc_root_hash):
        if (doc_root_hash==''):
            ErrorNotification.new('ERROR. doc_root_hash is EMPTY. Aborting publish_raw_tx ')
            return
        
        already_published=Utxo.query(Utxo.doc_fk==doc_root_hash).fetch()
        if len(already_published)>0:
            ErrorNotification.new('WARNING. doc_root_hash: '+doc_root_hash+ ' was already published. Aborting publish_raw_tx ')
            return
        
        unused_utxo=Utxo.get_doc()
        if not unused_utxo:
            ErrorNotification.new('ERROR. No bitcoins available to spend. doc_root_hash: ' + doc_root_hash)
            return
        
        unused_utxo.doc_fk=doc_root_hash
        txid, message=publish_data(binascii.unhexlify(doc_root_hash), unused_utxo)
                        
        k=ndb.Key('DocRoot', key_name)
        doc_root=k.get()
        if (txid!=None):
            doc_root.txid=txid
            doc_root.put()
            unused_utxo.date_bcast=test.utcnow()
            unused_utxo.put()
        else:
            ErrorNotification.new('ERROR. publish_data for doc_root_hash: '+doc_root_hash+' Message: '+message)
    
    def get(self):
        ErrorNotification.new('INFO: cron launched')
        flush_all()
        
        utc_today=test.utcnow()
        utc_yesterday=utc_today-datetime.timedelta(days=1)
        utc_tomorrow=utc_today+datetime.timedelta(days=1)
        
        key_name_today=utc_today.strftime("%Y-%m-%d")+'/00'
        key_name_yesterday=utc_yesterday.strftime("%Y-%m-%d")+'/00'
        key_name_tomorrow=utc_tomorrow.strftime("%Y-%m-%d")+'/00'
        
        selected=DocRoot.get_doc_by_key_name(key_name_today) 
        if not selected: 
            # It will enter here only on the first execution ever of cron
            DocRoot.new(key_name_today)

        selected=DocRoot.get_doc_by_key_name(key_name_tomorrow)
        if not selected:
            DocRoot.new(key_name_tomorrow)
        else:
            ErrorNotification.new('WARNING. Root already exists for tomorrow. Cron launched more than once?.')
            
        selected=DocRoot.get_doc_by_key_name(key_name_yesterday)
        if selected:
            if selected.doc_root_hash=='':
                # In transaction
                try:
                    doc_root_hash=self.get_merkle_chains(key_name_yesterday)
                    self.publish_raw_tx(key_name_yesterday, doc_root_hash)
                except:
                    ErrorNotification.new('ERROR: '+traceback.format_exc())
                    raise
            else:
                # It is possible that pushtx has failed in the previous cron but the root hash has already been calculated. 
                # If that is the case, retry
                ErrorNotification.new('WARNING. Root hash already calculated. Checking if root hash was already published...')
                self.publish_raw_tx(key_name_yesterday, selected.doc_root_hash)
        else:
            ErrorNotification.new('WARNING. Root for yesterday does not exist. Only possible first time ever.')          

        flush_all()