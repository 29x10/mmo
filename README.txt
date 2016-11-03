TradePlatform README

-install CouchDB
-modify CouchDB's local.ini
-uncomment the admin and set the password to qweasdzxc

-virtualenv mmo
-source bin/active
-pip install pyramid
-pip install CouchDB
-pip install paypal
-pip install cryptacular
-copy TradePlatform to mmo directory
-cd TradePlatform
-python setup.py develop

under TradePlatform directory
run pserve development.ini
