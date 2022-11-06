from venv import create
from rest_framework import serializers
from django.contrib.auth.models import User

class RegisterSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ('id','username','email','password')
    
    def create(self,data):
        user_obj = User.objects.create_user(**data)
        return user_obj
    
    def validate(self,data):
        flag = User.objects.filter(email = data.get('email')).exists()
        if flag:
            raise serializers.ValidationError("Email already exists")
        return data
        
class SerializeModelData(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ('id','username','email','password')
        
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(required=True)
    

class AccessTokenSerializer(serializers.Serializer):
    access_token = serializers.CharField(max_length=100, required=True)
    item_id = serializers.CharField(max_length=100, required=True)
    request_id = serializers.CharField(max_length=100, required=True)