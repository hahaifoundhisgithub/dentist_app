from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Allauth 認證網址 (Google 登入會用到)
    path('accounts/', include('allauth.urls')),

    path('clinic/', include('apps.clinic.urls')),
    path('member/', include('apps.member.urls')),
    path('', include('apps.core.urls')), 
]