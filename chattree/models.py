from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CASCADE
from django.db.models import SET_NULL
from django.utils.safestring import mark_safe
from mptt.models import MPTTModel, TreeForeignKey

# from simple_history import register
import logging

from telegram import TelegramError

logger = logging.getLogger('db')


def validate_token(value):
    try:
        from chattree.apps import setup_bot_and_webhook, chattree_bot_dispatchers

        if value not in chattree_bot_dispatchers:

            bot_dispatcher = setup_bot_and_webhook(value)
            chattree_bot_dispatchers.update({value: bot_dispatcher})
            logger.debug('on_save_chattree_bot_dispatchers: {0}'.format(chattree_bot_dispatchers))

    except TelegramError as e:
        raise ValidationError('Не удаётся зарегистрировать вебхук с'
                              ' этим токеном в телеграм: {0}!'.format(e))


class Bot(models.Model):

    name = models.CharField(max_length=120, verbose_name='Название, отображаемое в админке')
    chat_node = models.ForeignKey('chattree.ChatNode', verbose_name='Ветка вопросов и ответов',
                                  on_delete=SET_NULL, null=True, blank=True)

    start_message = models.TextField(verbose_name='Вступительное сообщение')
    end_message = models.TextField(verbose_name='Заключительное сообщение')

    token = models.CharField(max_length=64, verbose_name='Токен', unique=True,
                             help_text='<span style="color:red;font-weight:bold;">ВНИМАНИЕ: редактирование этого поля'
                                       ' может сломать Вашего бота.</a>\n Получить'
                                       ' токен для нового бота телеграм <br />можно с'
                                       ' использованием <a href="https://t.me/BotFather">'
                                       'https://t.me/BotFather</a>', validators=[validate_token])

    is_active = models.BooleanField(default=True, verbose_name='Бот включён/выключен')

    def __str__(self):
        return '{0} (вопросов {1})'.format(self.name, self.chat_node.get_descendants().count())

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from chattree.apps import setup_bot_and_webhook, chattree_bot_dispatchers

        if self.is_active and self.token not in chattree_bot_dispatchers:

            bot_dispatcher = setup_bot_and_webhook(self.token)
            chattree_bot_dispatchers.update({self.token: bot_dispatcher})
            logger.debug('on_save_chattree_bot_dispatchers: {0}'.format(chattree_bot_dispatchers))

        if not self.is_active and self.token in chattree_bot_dispatchers:
            bot_dispatcher = chattree_bot_dispatchers[self.token]
            bot_dispatcher.bot.delete_webhook()

    class Meta:
        # unique_together = (('parent', 'slug',))
        verbose_name_plural = 'Боты'
        verbose_name = 'Бот'


class ChatNode(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='children', db_index=True,
                            on_delete=models.CASCADE,
                            verbose_name='Родитель',
                            )
    answer = models.CharField(max_length=550, blank=True, null=True, verbose_name='Ответ')
    question = models.CharField(max_length=550, verbose_name='Вопрос')

    # class MPTTMeta:
    #     order_insertion_by = ['name']

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "question__icontains",)

    class Meta:
        # unique_together = (('parent', 'slug',))
        verbose_name_plural = 'Вопросы и ответы'
        verbose_name = 'Вопрос'

  # def get_slug_list(self):
  #   try:
  #     ancestors = self.get_ancestors(include_self=True)
  #   except:
  #     ancestors = []
  #   else:
  #     ancestors = [ i.slug for i in ancestors]
  #   slugs = []
  #   for i in range(len(ancestors)):
  #     slugs.append('/'.join(ancestors[:i+1]))
  #   return slugs

    def __str__(self):
            if self.parent:
                return '№{2}: {0} / {1}'.format(self.answer, self.question, self.pk)
            else:
                return '№{0} / {1}'.format(self.pk, self.question)


class ChatHistory(models.Model):
    """
    See https://core.telegram.org/bots/api#user

        https://core.telegram.org/bots/api#chat

    https://en.wikipedia.org/wiki/IETF_language_tag

    """
    user_id = models.PositiveIntegerField(verbose_name='ID пользователя телеграм')
    chat_id = models.PositiveIntegerField(verbose_name='ID чата телеграм')
    first_name = models.CharField(max_length=120, verbose_name='Имя')

    chat_node = models.ForeignKey('chattree.ChatNode',
                                  verbose_name='Вопрос, который задан пользователю',
                                  on_delete=SET_NULL, null=True, blank=True)
    bot = models.ForeignKey('chattree.Bot',
                                  verbose_name='Бот',
                                  on_delete=SET_NULL, null=True, blank=True)

    message_id = models.PositiveIntegerField(verbose_name='ID сообщения телеграм')

    username = models.CharField(max_length=255, verbose_name='Имя пользователя телеграм',
                                blank=True, null=True)
    last_name = models.CharField(max_length=255, verbose_name='Фамилия (Last name)',
                                 null=True, blank=True)
    language_code = models.CharField(max_length=255, verbose_name='IETF_language_tag',
                                 blank=True, null=True)

    message_date = models.DateTimeField()



