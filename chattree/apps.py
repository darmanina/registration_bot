from django.apps import AppConfig
from django.conf import settings
import logging

from telegram import TelegramError

logger = logging.getLogger('db')
chattree_bot_dispatchers = dict()


def setup_bot_and_webhook(bot_token):
    from chattree.treebot import setup_bot

    bot_dispatcher = setup_bot(token=bot_token)
    webhook_url = 'https://{0}/bot/{1}'.format(settings.HOST_NAME, bot_token)
    logger.debug('webhook_url: {0}'.format(webhook_url))
    bot_dispatcher.bot.set_webhook(url=webhook_url)

    return bot_dispatcher


class ChatTreeAppConfig(AppConfig):
    name = 'chattree'
    verbose_name = "Администрирование ботов Комитета «Гражданское содействие»"

    def ready(self):

        from chattree.models import Bot as ChatTreeBot

        for bot_token in ChatTreeBot.objects.all().values_list('token', 'is_active'):

            # Need this if in case if AppConfig.ready() runs twice
            if bot_token[0] not in chattree_bot_dispatchers and bot_token[1]:
                try:
                    bot_dispatcher = setup_bot_and_webhook(bot_token[0])
                    chattree_bot_dispatchers.update({bot_token[0]: bot_dispatcher})
                    logger.debug('chattree_bot_dispatchers: {0}'.format(chattree_bot_dispatchers))
                except TelegramError as e:
                    raise e

    #def ready(self):
    #   pass

