import datetime
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.ext.ndb import Key

import test

class Utxo(ndb.Model):
    txid=ndb.StringProperty()
    vout=ndb.IntegerProperty()
    satoshis=ndb.IntegerProperty()
    address=ndb.StringProperty()
    doc_fk=ndb.StringProperty()
    date_bcast=ndb.DateTimeProperty()

    @classmethod
    def get_doc(cls): # Get an unspent output
        selected=None
        try:
            selected = cls.query(cls.doc_fk == '0').iter().next()
        except StopIteration:
            pass  
        return selected
    
    @classmethod
    def new(cls, txid, vout, satoshis, address):
        d = cls(txid=txid, vout=vout, satoshis=satoshis, address=address, doc_fk='0', date_bcast=None)  
        d.put()
        return d


class DocLine(ndb.Model):
    content_hash=ndb.StringProperty()
    date_received=ndb.DateTimeProperty()
    doc_root=ndb.StringProperty()
    merkle_chain=ndb.TextProperty()

    @classmethod
    def get_doc(cls, content_hash):
        selected=None
        try:
            selected = cls.query(cls.content_hash == content_hash).iter().next()
        except StopIteration:
            pass
        return selected
    
    @classmethod
    def get_doc_unassigned(cls):
        selected=None
        try:
            selected = cls.query(cls.doc_root == '').order(cls.date_received).iter().next()
        except StopIteration:
            pass
        return selected
    
    @classmethod
    def get_doclines_from_root(cls, root_key_name_yesterday):
        k=ndb.Key('DocRoot', root_key_name_yesterday)
        
        selected=DocLine.query(ancestor=k).fetch() # Be careful if there are too many results! 
        return selected
    
    @classmethod
    def new(cls, parent, content_hash, date_received):
        d = cls(parent=parent, content_hash=content_hash, date_received=date_received, doc_root='', merkle_chain=db.Text('', encoding="utf-8"))
        d.put()
        return d
        
            
class DocRoot(ndb.Model):
    doc_root_hash=ndb.StringProperty()
    date_broadcast=ndb.DateTimeProperty()
    nodes=ndb.TextProperty()
    txid=ndb.StringProperty()
    
    @classmethod
    def get_doc(cls, doc_root_hash):
        selected=None
        try:
            selected = cls.query(cls.doc_root_hash==doc_root_hash).iter().next()
        except StopIteration:
            pass
        return selected
    
    @classmethod
    def get_doc_by_key_name(cls, key_name):
        k=ndb.Key('DocRoot', key_name)
        selected=k.get()
        return selected
    
    @classmethod
    def new(cls, key_name):
        # http://stackoverflow.com/questions/24332648/google-app-engine-no-key-name-attribute
        d=cls(id=key_name, doc_root_hash='', date_broadcast=None, nodes=db.Text('', encoding='utf-8'), txid='')
        d.put()
        return d

    
class ErrorNotification(ndb.Model):
    message=ndb.TextProperty()
    date_received=ndb.DateTimeProperty()

    @classmethod
    def new(cls, message):        
        d = cls(message=db.Text(message) if isinstance(message,unicode) else db.Text(message, encoding='utf-8'),
                date_received=test.utcnow())
        d.put()
        return d