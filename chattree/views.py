from django.http import Http404
from django.views.generic import DetailView
from rest_framework.response import Response
from django.http import HttpResponse
from chattree.treebot import setup_bot
from rest_framework.utils import json
from rest_framework.views import APIView
from telegram import Update
import logging

from chattree.models import ChatNode

logger = logging.getLogger('db')


class UpdateBot(APIView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("The bot URL is accessible")

    def post(self, request, *args, **kwargs):
        from chattree.apps import chattree_bot_dispatchers

        token = self.kwargs['token']
        logger.debug('token_in_view: {0}'.format(token))
        logger.debug('chattree_bot_dispatchers_in_view: {0}'.format(chattree_bot_dispatchers))

        try:
            bot_dispatcher = chattree_bot_dispatchers[token]
        except KeyError:
            return Http404()
        else:
            request_json = request.body.decode('UTF-8')
            update = Update.de_json(json.loads(request_json), bot_dispatcher.bot)
            logger.debug(update)
            bot_dispatcher.process_update(update)
            response = Response({'code': 200, })

            return response


class ChatNodeDetailView(DetailView):
    model = ChatNode
    template_name = 'chatnode.html'

