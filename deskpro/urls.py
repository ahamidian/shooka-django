"""deskpro URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

from app.views import *

router = routers.DefaultRouter()
router.register(r'ticket', TicketViewSet, base_name='ticket')
router.register(r'agent', AgentViewSet, base_name='agent')
router.register(r'team', TeamViewSet, base_name='team')
router.register(r'tag', TagViewSet, base_name='tag')




urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('summernote/', include('django_summernote.urls')),
    path('tickets/', tickets_page),
    path('ticket-setting/<int:pk>/', submit_ticket_setting),
    path('ticket/<int:pk>/', ticket_detail),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),
    path('profile/', profile, name='profile'),
    path('user/<int:pk>/', user_detail),
    path('api/', include(router.urls)),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)