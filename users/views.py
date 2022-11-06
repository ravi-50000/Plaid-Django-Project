import os,json
from django.shortcuts import render,HttpResponse
from rest_framework.response import Response
from users.serializers import *
from rest_framework import status, pagination
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth import login
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, logout, login
from django.core.exceptions import ObjectDoesNotExist
import plaid,json,datetime
from users.models import *
from django.views.decorators.csrf import csrf_exempt
from users.tasks import *
from dotenv import load_dotenv
load_dotenv()

client_id=os.getenv('client_id')
secret=os.getenv('secret')
environment=os.getenv('environment')

client = plaid.Client(client_id=client_id, secret=secret, environment=environment)


# Create your views here.
class RegisterAPI(APIView):
    def get(self, req):
        return Response({"Message": "This is a get method"}, status = status.HTTP_200_OK)
    
    def post(self, req):
        obj =  RegisterSerializer(data = req.data)
        if obj.is_valid():
            obj.save()
            return Response({'Message':'Signed-up'},status = status.HTTP_200_OK)

        return Response(obj.errors, status = status.HTTP_400_BAD_REQUEST)
    
    
class GetAllUsersData(APIView):
    def get(self,req):
        obj = User.objects.all()
        serialize =  SerializeModelData(obj,many=True)
        return Response(serialize.data)
    
class LoginApi(APIView):
    def post(self,req):
        login_serialize = LoginSerializer(data = req.data)
        
        if login_serialize.is_valid():
            username = login_serialize.validated_data['username']
            password = login_serialize.validated_data['password']
            user = authenticate(username=username,password=password)
            if user is None:
                return Response("Invalid Credentials")
            else:
                login(req,user)
            return Response({"Message":"Logged in Successfully"},status=status.HTTP_200_OK)
            
        return Response(login_serialize.errors,status=status.HTTP_400_BAD_REQUEST)
    
class LogOutApi(APIView):
    def post(self,req):
        if req.user.is_authenticated:
            logout(req)
            return Response({"Message":"Logged out successfully"},status=status.HTTP_200_OK)
        else:
            return Response({"Message":"No user logged in"})
    

class GetLinkToken(APIView):
    def post(self,request):
        if request.user.is_authenticated:
            try:
                request = {
                    'user': {
                        'client_user_id': client_id,
                        },
                    "client_name" : "Plaid Test App",
                    'client_user_id': client_id,
                    'products': ['auth', 'transactions'],
                    'webhook': 'https://sample-webhook-uri.com',
                    'country_codes': ['US'],
                    'language': 'en',
                    'link_customization_name': 'default',
                    'account_filters': {
                        'depository': {
                            'account_subtypes': ['checking', 'savings'],
                            },
                    }
                }
                response = client.LinkToken.create(request)
                StoreLinkItem.objects.create(request_id = response['request_id'])
                return Response(response,status=status.HTTP_200_OK)
            
            except Exception as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"Message":"No user logged in"})
        

class getAccessToken(APIView):
    def post(self,request):
        request_data = request.POST
        public_token = request_data.get('public_token')
        print("public token is ",public_token)
        try:
            exchange_response = client.Item.public_token.exchange(public_token)
            serializer = AccessTokenSerializer(data=exchange_response)
            if serializer.is_valid(raise_exception=True):
                access_token = serializer.validated_data['access_token']
                BankItemModel.objects.create(bank_item_id=serializer.validated_data['item_id'], access_token=access_token,request_id=serializer.validated_data['request_id'],user=self.request.user)
                print("access token is ",access_token)
                
                try:
                    fetch_transactions.delay(access_token)  #async task
                    
                except Exception as e:
                    print('Task Failed due to :', e)
                    
            return Response(data = exchange_response, status = status.HTTP_200_OK)
                                 
        except plaid.errors.PlaidError as e:
            return Response({'errors from plaid: ': e}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'errors': e},status=status.HTTP_400_BAD_REQUEST)
     
     

def link(request):
    if request.user.is_authenticated:
      return render(request, "link.html")
    
    return HttpResponse("No user logged in")


class getItems(APIView):
    
	def get(self,request):
         if request.user.is_authenticated:
             try:
                bank_item = BankItemModel.objects.filter(user= request.user)
                get_item_data =[]
                access_token_obj_list = bank_item.values('access_token')
                for i in access_token_obj_list:
                    response = client.Item.get(i['access_token'])
                    item = response['item']
                    get_item_data.append(item)
                    #  print(item)
                return Response({"Items are :" :get_item_data}, status= status.HTTP_200_OK)
            
             except Exception as e:
                 return Response({'errors: e'}, status= status.HTTP_400_BAD_REQUEST)
        
         return Response({"Message":"No user logged in"})
       
class getAccounts(APIView):
    
	def get(self,request):
         if request.user.is_authenticated:
             try:
                bank_item = BankItemModel.objects.filter(user=self.request.user)
                get_accounts_data =[]
                access_token_obj_list = bank_item.values('access_token')
                for i in access_token_obj_list:
                    response = client.Accounts.get(i['access_token'])
                    accounts = response['accounts']
                    get_accounts_data.append(accounts)
            
                if len(get_accounts_data):
                    return Response({"Accounts are :" :{len(get_accounts_data):get_accounts_data}}, status= status.HTTP_200_OK)
                
                return Response({"Message":"No Accounts Present!"}, status= status.HTTP_200_OK)
            
             except Exception as e:
                  return Response({'errors: e'}, status= status.HTTP_400_BAD_REQUEST)
         
         return Response({"Message":"No user logged in"})
     
class getTransactions(APIView):
        
    def get(self,request):
         if request.user.is_authenticated:
             try:
                bank_item = BankItemModel.objects.filter(user=self.request.user)
                get_transactions_data =[]
                access_token_obj_list = bank_item.values('access_token')
                for i in access_token_obj_list:
                    response = client.Transactions.get(i['access_token'],start_date = '{:%Y-%m-%d}'.format(datetime.datetime.now() + datetime.timedelta(-100)),end_date = '{:%Y-%m-%d}'.format(datetime.datetime.now()))
                    get_transactions_data.append(response['transactions'])
                    # print(response)
                
                return Response({"Transactions are : ": {len(get_transactions_data):get_transactions_data}}, status= status.HTTP_200_OK) 
             
             except Exception as e:
                return Response({'errors: e'}, status= status.HTTP_400_BAD_REQUEST)
         
         return Response({"Message":"No user logged in"})
     
@csrf_exempt
def webhook(req):
    request_ = json.loads(req.body.decode())
    webhook_type = request_.get('webhook_type')
    webhook_code = request_.get('webhook_code')

    if webhook_type == 'TRANSACTIONS':
        item_id = request_.get('item_id')
        if webhook_code == 'TRANSACTIONS_REMOVED':
                removed_transactions = request_.get('removed_transactions')
                delete_transactions.delay(removed_transactions)

        else:
                new_transactions = request_.get('new_transactions')
                fetch_transactions.delay(None, item_id, new_transactions)

        return HttpResponse('Webhook received', status=status.HTTP_200_OK)
    
    return HttpResponse("Wrong webhook type", status = status.HTTP_400_BAD_REQUEST)