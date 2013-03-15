from paypal import PayPalConfig, PayPalInterface

__author__ = 'binleixue'
CONFIG = PayPalConfig(API_USERNAME = "kongpo0412-facilitator_api1.gmail.com",
    API_PASSWORD = "1362817375",
    API_SIGNATURE = "AFcWxV21C7fd0v3bYYYRCpSSRl31AbxqObt4CKqgaCni7myjfgFGCPW8",
    DEBUG_LEVEL=0)
interface = PayPalInterface(CONFIG)
