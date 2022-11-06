from django.contrib import admin
from users.models import *

# Register your models here.
admin.site.register(StoreLinkItem)
admin.site.register(BankItemModel)
admin.site.register(AccountModel)
admin.site.register(TransactionModel)