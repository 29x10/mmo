from datetime import datetime
from couchdb.mapping import Document, IntegerField, TextField, ViewField, ListField


class Zhanghao(Document):
    db_type = TextField(default='zhanghao')
    name = TextField()
    level = IntegerField()
    seller = TextField()
    gmt_create = TextField()
    price = IntegerField()
    status = IntegerField(default=1)
    tags = ListField(TextField())

    by_seller = ViewField('zhanghao', '''
        function(doc) {
            if (doc.db_type == 'zhanghao') {
                emit([doc.seller, doc.gmt_create], doc);
            }
        }''')

    by_buyer = ViewField('zhanghao', '''
        function(doc) {
            if (doc.db_type == 'zhanghao' && doc.buyer) {
                emit([doc.buyer, doc.gmt_success], doc);
            }
        }''')

    by_tag = ViewField('zhanghao', '''
        function(doc) {
            if (doc.db_type == 'zhanghao') {
                doc.tags.forEach(function(tag) {
                    emit(tag, null);
                });
            }
        }''', '''
        function(keys, values) {
            return true;
        }''')

    each_tag = ViewField('zhanghao', '''
        function(doc) {
            if (doc.db_type == 'zhanghao' && doc.status == 1) {
                doc.tags.forEach(function(tag) {
                    emit([tag, doc.gmt_create], doc);
                });
            }
        }''')

    def __init__(self, name, level, seller, price, tags):
        Document.__init__(self)
        self.name = name
        self.level = level
        self.seller = seller
        self.gmt_create = str(datetime.now())
        self.price = price
        self.tags = tags