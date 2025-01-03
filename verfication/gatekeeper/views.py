from django.shortcuts import render
import jwt
from .decorators import jwt_required
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import HttpResponse
import requests
import json
import re
from io import BytesIO
from django.conf import settings
from .models import logged_in_users
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


def say_hi(request):
    if request.method == 'GET':
        response = requests.get(f'{back_path}hello')
        return JsonResponse({'message':response.json()},status=200)
    return JsonResponse({'error':'not allowed'},status=200)

@csrf_exempt
def register(request):
    if request.method =="POST":
         try:
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
         except:
              return JsonResponse({"error": "invalid request"}, status=400)

@csrf_exempt
def Log_in(request):
    if request.method =="POST":
         try:
               data = json.loads(request.body)
               username = data.get("username")
               password = data.get("password")
               logged_in=logged_in_users.objects.filter(username=username)
               if not logged_in:
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                         new_user=logged_in_users(username=username)
                         new_user.save()
                         token = generate_jwt(user)
                         return JsonResponse({"message":"log in succuessfull","token":{'token':token}}, status=200)
                    else:
                         
                         return JsonResponse({"error": "Invalid username or password"}, status=400)
               else:
                   
                    return JsonResponse({"error": "user already logged in "}, status=400)  
         except:
               return JsonResponse({"error": "user authentication failed"}, status=400)  

@jwt_required
@csrf_exempt
def log_out(request):
     if request.method == "GET":
          auth_header = request.headers.get('Authorization')
          token = auth_header.split(" ")[1]
          payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
          username = payload['username']
          logged_in=logged_in_users.objects.filter(username=username)
          if logged_in:
               logged_in.delete()
          return JsonResponse({"message": "log out successfull"}, status=200)
  
@jwt_required
@csrf_exempt
def get_file(request):
     if request.method == "POST":
          try:
               auth_header = request.headers.get('Authorization')
               token = auth_header.split(" ")[1]
               payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
               username = payload['username']
               csv_file= request.FILES['file']
               files = {'file': csv_file}
               data = {'username': username}
               
               response = requests.post(f'{back_path}file', files=files, data=data)
               data=response.json()
               return JsonResponse({"message":data['message']} , status=200)
          except:
               return JsonResponse({"error":'user is not logged in'} , status=400)

@jwt_required
@csrf_exempt
def get_Data(request):
    if request.method =='POST':
         try:
               auth_header = request.headers.get('Authorization')
               token = auth_header.split(" ")[1]
               query=request.POST.get("query", "")
               payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
               username = payload['username']
               
               data = {'username': username,'query': query}
               response = requests.post(f'{back_path}query', data=data)
               data=response.json()
               if response.status_code==200 :
                         if data['type']=='read':
                              return JsonResponse({"message":data['message'],"column":data['column'],"rows":data['rows'],"type":"read"} , status=200)
                         else:
                              return JsonResponse({"message":data['message'],"type":"write","dataset":data['dataset']} , status=200)
               else:
                    return JsonResponse({"message":"bad query","error":data['error']} , status=201)
         except:
              return JsonResponse({"error":'user is not logged in'} , status=400)
def refresh_token(request):
     if request.method == "GET":
          auth_header = request.headers.get('Authorization')
          if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Unauthorized"}, status=401)
          token = auth_header.split(" ")[1]
          try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            exp = payload.get('exp', 0)
            if datetime.utcnow().timestamp() > exp - 900:  
                new_payload = {
                    'id': payload['id'],
                    'username': payload['username'],
                    'exp': datetime.utcnow() + timedelta(hours=3),  # New expiration time
                }
                new_token = jwt.encode(new_payload, settings.SECRET_KEY, algorithm='HS256')
                return JsonResponse({"token": new_token}, status=200)
            else:
                return JsonResponse({"message": "Token not yet close to expiry"}, status=200)
          except jwt.ExpiredSignatureError:
             return JsonResponse({"error": "Token expired"}, status=401)
          except jwt.InvalidTokenError:
             return JsonResponse({"error": "Invalid token"}, status=401)

@jwt_required
def load_latest(request):
     if request.method == "GET":
          try:
               auth_header = request.headers.get('Authorization')
               token = auth_header.split(" ")[1]
               payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
               username = payload['username']
               response = requests.post(f'{back_path}refresh', data={'username':username})
               data=response.json()
               return JsonResponse({"message":data['message'],"type":"write","dataset":data['dataset']} , status=200)
          except:
                return JsonResponse({"error":'user is not logged in'} , status=400)
@jwt_required
def download_sheet(request):
     if request.method == "GET":
          try:
               auth_header = request.headers.get('Authorization')
               token = auth_header.split(" ")[1]
               payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
               username = payload['username']
               response = requests.post(f'{back_path}download', data={'username':username})
               file_content = BytesIO(response.content)
               response = HttpResponse(
               file_content,
               content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
               ) 
               response['Content-Disposition'] = f'attachment; filename="{username}_data.xlsx"'
               return response
          except:
               return JsonResponse({"error":'user is not logged in'} , status=400)
          
