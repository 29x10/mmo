from couchdb.mapping import ViewField
from couchdb.mapping import Document
from couchdb.mapping import TextField
from cryptacular.bcrypt import BCRYPTPasswordManager

manager = BCRYPTPasswordManager()

class Account(Document):
    db_type = TextField(default='account')
    mail = TextField()
    passwd = TextField()

   # @ViewField.define('account')
   # def by_mail(doc):
   #     if doc['db_type'] == 'account':
   #         yield doc['mail'], doc['password']

    by_mail = ViewField('account', '''
        function(doc) {
            if (doc.db_type == 'account') {
                emit(doc.mail, doc.passwd);
            }
        }''')

    def __init__(self, mail, passwd):
        Document.__init__(self)
        self.mail = mail
        self.passwd = manager.encode(passwd)