from django.urls import path
from . import views

urlpatterns = [
    path('hello', views.say_hi, name='home'),
    path('regist', views.register, name='register user'),
    path('login', views.Log_in, name='log in user'),
    path('logout', views.log_out, name='log out user'),
    path('file',views.get_file,name="get excel")
]
