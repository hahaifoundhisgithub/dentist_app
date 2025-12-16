from django.urls import path
from . import views  # 1. 改回引用自己的 views

urlpatterns = [
    # 2. 改回指向 member 自己的 home (假設您的 view 叫做 home 或 index)
    path('', views.home, name='member_home'), 
]