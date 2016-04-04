import webapp2

from doc import TestHandler, CheckContentHandler, BroadcastDailyHandler

app = webapp2.WSGIApplication([
    ('/api/tx/send', TestHandler),
    ('/api/content/check', CheckContentHandler),
    ('/api/broadcast/daily', BroadcastDailyHandler)
], debug=True)
