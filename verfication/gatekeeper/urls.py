from django.urls import path
from . import views

urlpatterns = [
    path('hello', views.say_hi, name='home'),
    path('regist', views.register, name='register user'),
    path('login', views.Log_in, name='log in user'),
    path('file',views.get_file,name="get excel"),
    path('refresh',views.refresh_token,name="refresh toekn"),
    path('query',views.get_Data,name="run queries"),
    path('reload',views.load_latest,name="reload latest datasheet"),
    path('download',views.download_sheet,name="download datasheet"),
]
