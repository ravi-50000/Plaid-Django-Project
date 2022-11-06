from django.urls import path
from users.views import *


urlpatterns = [
    path('register/', RegisterAPI.as_view(), name = 'register'),
    path('getallusersdata/', GetAllUsersData.as_view(), name = 'allUserData'),
    path('login/', LoginApi.as_view(),name = 'login'),
    path('logout/', LogOutApi.as_view(), name = 'logout'),
    path('api/link/token/', GetLinkToken.as_view(), name = 'linkToken'), 
    path('link/',link, name='link'),
    path('get_access_token/', getAccessToken.as_view(), name = 'accessToken'),
    path('get_items/', getItems.as_view(), name = 'items'),
    path('get_accounts/', getAccounts.as_view(), name = 'accounts'),
    path('get_transactions/', getTransactions.as_view(), name = 'transactions'),
    path('webhook/', webhook, name = 'webhook'),
]