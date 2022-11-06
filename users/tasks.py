from __future__ import absolute_import, unicode_literals
from celery import shared_task
import datetime
import plaid,os
from users.models import *
from dotenv import load_dotenv
load_dotenv()

client_id=os.getenv('client_id')
secret=os.getenv('secret')
environment=os.getenv('environment')
client = plaid.Client(client_id=client_id, secret=secret, environment=environment)

@shared_task
def delete_transactions(removed_transactions):
    TransactionModel.objects.filter(transaction_id__in = removed_transactions).delete()

@shared_task
def fetch_transactions(access_token, bank_item_id = None, new_transactions=40):
    if access_token is None :
        access_token = str(BankItemModel.objects.get(bank_item_id = bank_item_id).access_token)
   
    start_date = '{:%Y-%m-%d}'.format(
        datetime.datetime.now() + datetime.timedelta(-730))
    end_date = '{:%Y-%m-%d}'.format(datetime.datetime.now())

    response = client.Transactions.get(access_token, start_date,end_date,count = new_transactions)
    
    accounts = response['accounts']
    transactions = response['transactions']
    
    if bank_item_id is None:
        bank_item_id = response['item']['item_id']
    bank_item = BankItemModel.objects.get(bank_item_id=bank_item_id)
    
    for acc in accounts:
        try:
            acc_obj = AccountModel.objects.get(account_id = acc['account_id'])
            acc_obj.balance_available = acc['balances']['available']
            acc_obj.balance_current = acc['balances']['current']
            acc_obj.save()
        
        except Exception as e:
            print(e)
            acc_obj_create = AccountModel.objects.create(account_id = acc['account_id'], bank_item=bank_item, balance_available = acc['balances']['available'], balance_current = acc['balances']['current'])
        
    # transaction - 1,2,3
    #  webhook - 1,2,1,3,4
    
    
    transaction_list = TransactionModel.objects.filter(
        account__bank_item=bank_item)

    for transaction in transactions:
        try:
            transaction_obj = transaction_list.get(transaction_id = transaction['transaction_id'])
            transaction_obj.amount = transaction['amount']
            transaction_obj.pending = transaction['pending']
            transaction_obj.save()
                
        except Exception as e:
            print(e)
            account_ = AccountModel.objects.get(
                account_id=transaction['account_id'])

            transaction_obj = TransactionModel.objects.create(
                transaction_id=transaction['transaction_id'],
                account=account_,
                amount=transaction['amount'],
                date=transaction['date'],
                name=transaction['name'],
                pending=transaction['pending'])