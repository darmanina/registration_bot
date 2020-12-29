from django.apps import AppConfig
from django.conf import settings
import logging

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

        for bot_token in ChatTreeBot.objects.all().values_list('token', flat=True):

            # Need this if in case if AppConfig.ready() runs twice
            if bot_token not in chattree_bot_dispatchers:

                bot_dispatcher = setup_bot_and_webhook(bot_token)
                chattree_bot_dispatchers.update({bot_token: bot_dispatcher})
                logger.debug('chattree_bot_dispatchers: {0}'.format(chattree_bot_dispatchers))

    #def ready(self):
    #   pass

