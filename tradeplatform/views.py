# -*- coding: UTF-8 -*-
from datetime import datetime
from couchdb import Document, ResourceNotFound
from couchdb.client import ViewResults
from cryptacular.bcrypt import BCRYPTPasswordManager
from paypal.exceptions import PayPalAPIResponseError
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPForbidden
from pyramid.response import Response
from pyramid.security import remember, authenticated_userid, forget
from modules.account import Account
from pyramid.view import view_config
from tradeplatform.deal.config import interface
from tradeplatform.modules.zhanghao import Zhanghao

manager = BCRYPTPasswordManager()

@view_config(renderer='index.html', route_name='home')
def index(request):
    return dict()

@view_config(context='pyramid.httpexceptions.HTTPForbidden', renderer='login.html')
@view_config(name='login', renderer='login.html')
def login(request):
    if 'login.submit' in request.params:
        email = request.params['mail']
        passwd = request.params['passwd']
        map_fun = Account.by_mail.map_fun
        db = request.db
        result = db.query(map_fun, key=email)
        if len(result):
            hashed_passwd = result.rows[0].value
            if manager.check(hashed_passwd, passwd):
                headers = remember(request, email)
                return HTTPFound(location = '/', headers = headers)
        raise HTTPNotFound
    return dict(post_url = request.path)

@view_config(name='signup', renderer='signup.html')
def sign_up(request):
    if 'signup.submit' in request.params:
        username = request.params['mail']
        passwd = request.params['passwd']
        passwd1 = request.params['passwd1']
        if passwd != passwd1:
            raise HTTPNotFound
        map_fun = Account.by_mail.map_fun
        db = request.db
        result = db.query(map_fun, key=username)
        if len(result):
            raise HTTPNotFound
        account = Account(username, passwd)
        db = request.db
        account.store(db)
        headers = remember(request, username)
        return HTTPFound(location = '/', headers = headers)
    return dict(post_url = request.path)

@view_config(name='logout')
def log_out(request):
    headers = forget(request)
    return HTTPFound(location='/', headers=headers)

@view_config(name='sell', renderer='sell.html', permission='view')
def sell(request):
    if 'sell.submit' in request.params:
        name = request.params['name']
        level = request.params['level']
        price = request.params['price']
        tags = request.params['tags'].split(" ")
        seller = authenticated_userid(request)
        zhanghao = Zhanghao(name, int(level), seller, int(price), tags)
        db = request.db
        zhanghao.store(db)
        return HTTPFound(location='/')
    if 'sell.cancel' in request.params:
        return HTTPFound(location='/')
    return dict(post_url = request.path)

@view_config(name='account', renderer='account.html', permission='view')
def account(request):
    return dict()

@view_config(name='selling', renderer='selling.html', permission='view')
def selling(request):
    start_key = request.params.get('start_key', {})
    db = request.db
    map_fun = Zhanghao.by_seller.map_fun
    seller = authenticated_userid(request)
    selling_list = db.query(map_fun, startkey=[seller, start_key], endkey=[seller], descending=True, limit=3)
    if len(selling_list):
        L = []
        if len(selling_list) == 3:
            start_key=selling_list.rows[-1].key[1]
            for row in selling_list.rows[:-1]:
                L.append(row.value)
            return dict(list = L, start_key=start_key)
        else:
            for item in selling_list:
                L.append(item.value)
            return dict(list = L, start_key={})
    return dict(list=[], start_key={})

@view_config(route_name='item', context=Document, permission='view', renderer='detail.html')
def detail(context, request):
    if 'buy.submit' in request.params:
        amount = str(context['price']) + '.00'
        outer_id = context['_id']
        item_name = context['name']
        cancelurl = "http://localhost:6543/item/" + outer_id
        try:
            setexp_response = interface.set_express_checkout(PAYMENTREQUEST_0_AMT=amount,
            returnurl="http://localhost:6543/trade_success", cancelurl=cancelurl,
            REQCONFIRMSHIPPING='0', NOSHIPPING='1', PAYMENTREQUEST_0_INVNUM=outer_id,
            PAYMENTREQUEST_0_ITEMAMT=amount, L_PAYMENTREQUEST_0_NAME0=item_name,
            L_PAYMENTREQUEST_0_DESC0=item_name, L_PAYMENTREQUEST_0_AMT0=amount,
            L_PAYMENTREQUEST_0_QTY0='1')
        except PayPalAPIResponseError:
            return HTTPNotFound
        token = setexp_response.token
        redir_url = interface.generate_express_checkout_redirect_url(token)
        return HTTPFound(location=redir_url)
    return dict(item=context, post_url=request.path)

@view_config(name='trade_success')
def do_trade(request):
    payer_id = request.params['PayerID']
    token = request.params['token']
    try:
        getexp_response = interface.get_express_checkout_details(token=token)
        amount =getexp_response['PAYMENTREQUEST_0_AMT']
        trade_result = interface.do_express_checkout_payment(PAYMENTREQUEST_0_AMT=amount,
        payerId=payer_id, token=token, PAYMENTREQUEST_0_PAYMENTACTION='Sale')
    except PayPalAPIResponseError:
        return HTTPNotFound
    id = getexp_response['PAYMENTREQUEST_0_INVNUM']
    db = request.db
    if not trade_result:
        redir_url = '/item/' + id
        return HTTPFound(location=redir_url)
    try:
        item = db[id]
    except ResourceNotFound:
        raise HTTPNotFound
    item['paypal_id'] = trade_result['PAYMENTINFO_0_TRANSACTIONID']
    item['status'] = 2
    item['buyer'] = authenticated_userid(request)
    item['gmt_success'] = str(datetime.now())
    db[id] = item
    return HTTPFound(location='/buying')

@view_config(name='buying', renderer='buying.html', permission='view')
def buying(request):
    start_key = request.params.get('start_key', {})
    db = request.db
    map_fun = Zhanghao.by_buyer.map_fun
    buyer = authenticated_userid(request)
    buying_list = db.query(map_fun, startkey=[buyer, start_key], endkey=[buyer], descending=True, limit=3)
    if len(buying_list):
        L = []
        if len(buying_list) == 3:
            start_key=buying_list.rows[-1].key[1]
            for row in buying_list.rows[:-1]:
                L.append(row.value)
            return dict(list = L, start_key=start_key)
        else:
            for item in buying_list:
                L.append(item.value)
            return dict(list = L, start_key={})
    return dict(list=[], start_key={})

@view_config(name='refund', permission='view')
def apply_refund(request):
    id = request.params['id']
    db = request.db
    try:
        item = db[id]
    except ResourceNotFound:
        raise HTTPNotFound
    if item['status'] != 2:
        raise HTTPNotFound
    buyer = item['buyer']
    user = authenticated_userid(request)
    if buyer != user:
        raise HTTPForbidden
    item['status'] = 3
    db[id] = item
    return HTTPFound(location='/buying')

@view_config(name='doRefund', permission='view')
def do_refund(request):
    id = request.params['id']
    db = request.db
    try:
        item = db[id]
    except ResourceNotFound:
        raise HTTPNotFound
    if item['status'] != 3:
        raise HTTPNotFound
    seller = item['seller']
    user = authenticated_userid(request)
    if seller != user:
        raise HTTPForbidden
    outer_id = item['paypal_id']
    try:
        refund_response = interface.refund_transaction(TRANSACTIONID=outer_id)
    except PayPalAPIResponseError:
        raise HTTPNotFound
    item['refund_id'] = refund_response['REFUNDTRANSACTIONID']
    item['status'] = 4
    db[id] = item
    return HTTPFound(location='/selling')

@view_config(name='cancelRefund', permission='view')
def cancel_refund(request):
    id = request.params['id']
    db = request.db
    try:
        item = db[id]
    except ResourceNotFound:
        raise HTTPNotFound
    if item['status'] != 3:
        raise HTTPNotFound
    seller = item['seller']
    buyer = item['buyer']
    user = authenticated_userid(request)
    if seller != user and buyer != user:
        raise HTTPForbidden
    item['status'] = 2
    db[id] = item
    if user == seller:
        return HTTPFound(location='/selling')
    return HTTPFound(location='/buying')


@view_config(route_name="tag", permission="view", context=ViewResults, renderer="instock.html")
def tag_view(context, request):
    L = []
    for item in context:
        L.append(item.value)
    return dict(list = L)