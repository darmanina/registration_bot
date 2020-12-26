"""chattree URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.conf.urls import url
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from chattree.views import UpdateBot, ChatNodeDetailView
from chattree.models import ChatNode
from django.views.generic import ListView
from grappelli.views.related import AutocompleteLookup

from chattree.grappelli_related import CustomAutocompleteLookup, CustomRelatedLookup

TELEGRAM_TOKEN_REGEX = r'[0-9]{9}:[a-zA-Z0-9_-]{35}'

#r'(?P<pk>\d+)/(?P<slug>[-\w\d]+)$'

urlpatterns = [
    url(r'grappelli/lookup/related/$', CustomRelatedLookup.as_view(), name="grp_related_lookup"),
    url(r'grappelli/lookup/autocomplete/$', CustomAutocompleteLookup.as_view(), name="grp_autocomplete_lookup"),
    path('grappelli/', include('grappelli.urls')), # grappelli URLS
    path('admin/', admin.site.urls),
    path('admin/log_viewer/', include('log_viewer.urls')),
    url(r'^bot/(?P<token>[\:a-zA-Z0-9_-]{46})$', csrf_exempt(UpdateBot.as_view()), name='update'),
    path('c/<int:pk>/', ChatNodeDetailView.as_view(), name='chatnode-detail'),
    url(r'^full_chat_tree/', ListView.as_view(
        model=ChatNode,
        template_name='full_chat_tree.html',
        queryset=ChatNode.objects.all
        ),
        name='full_chat_tree',),
]
