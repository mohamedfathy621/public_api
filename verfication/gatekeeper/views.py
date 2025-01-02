from django.shortcuts import render
import jwt
from .decorators import jwt_required
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import requests
import json
import re
from django.conf import settings
# Create your views here.
back_path='http://127.0.0.1:8000/transformer/'
SECRET_KEY = settings.SECRET_KEY
def generate_jwt(user):
    payload = {
        'id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(hours=3),  # Token valid for 1 hour
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def run_validations(username,password):
     if re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$",password) and re.match(r"^[A-Za-z\s]{4,20}$",username):
          return True
     return False

@login_required
def say_hi(request):
    if request.method == 'GET':
        ##response = requests.get(f'{back_path}hello')
        return JsonResponse({'message':"it works"},status=200)

@csrf_exempt
def register(request):
    if request.method =="POST":
         data = json.loads(request.body)
         username = data.get('username')
         password = data.get('password')
         if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already exists."}, status=400)
         if run_validations(username,password):
            user = User.objects.create_user(username=username,password=password)
            return JsonResponse({"message":"user register successfull"},status=200)
         else:
                return JsonResponse({"error": "bad username or password"}, status=400)

@csrf_exempt
def Log_in(request):
    if request.method =="POST":
         data = json.loads(request.body)
         username = data.get("username")
         password = data.get("password")
         user = authenticate(request, username=username, password=password)
         if user is not None:
              token = generate_jwt(user)
              return JsonResponse({"message":"log in succuessfull","token":{'token':token}}, status=200)
         else:
                return JsonResponse({"error": "Invalid username or password"}, status=400)
@csrf_exempt
def log_out(request):
     if request.method == "POST":
          username=request.POST.get('username')
          return JsonResponse({"message":"log out succuessfull"}, status=200)

@jwt_required
@csrf_exempt
def get_file(request):
     if request.method == "POST":
          username= request.POST.get('username',"")
          csv_file= request.FILES['file']
          files = {'file': csv_file}
          data = {'username': username}
          response = requests.post(f'{back_path}file', files=files, data=data)
          data=response.json()
          return JsonResponse({"message":data['message']} , status=200)
     return JsonResponse({"error":'user is not logged in'} , status=400)