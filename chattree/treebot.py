import functools
from asgiref.sync import async_to_sync
from django.conf import settings
from telegram import CallbackQuery
from telegram import ChatAction
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import KeyboardButton
from telegram import ParseMode
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram import TelegramError
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram import Bot
from functools import wraps
from telegram.ext import ConversationHandler
from telegram.ext import Dispatcher
import logging
import asyncio
from datetime import datetime
import amplitude

amplitude_logger = amplitude.AmplitudeLogger(api_key=settings.AMPLITUDE_API_KEY)
logger = logging.getLogger('db')


def log_exception(function):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except:
            # log the exception
            err = "There was an exception in  "
            err += function.__name__
            logger.exception(err)
            # re-raise the exception
            raise
    return wrapper


@log_exception
def save_message_history(user, message, chat_node_pk, bot_pk):
    
    try:
        username = getattr(user, 'username', None)
        # logger.debug('hasattr(user, "username"): {0}'.format(hasattr(user, 'username')))
        last_name = getattr(user, 'last_name', None)

        event_args = {'user_id': str(user.id),
                      
                      'event_properties': {
                        'user_first_name': user.first_name,
                        'message': str(message.text),
                        'last_name': last_name,
                        'username': username,
                        'language_code': str(user.language_code),
                        'chat_id': str(message.chat.id), },

                      'event_type': 'outgoing_message',
                  }
        #              user_id='.'.join([user.id, user.first_name, ]),


        event = amplitude_logger.create_event(**event_args)

        # send event to amplitude
        amplitude_logger.log_event(event)
    except Exception as e:
        logger.debug(e)
    else:
        logger.debug('event: {0}'.format(event))

    return
    logger.debug('===== save_message_history: START =====')

    logger.debug('user: {0}'.format(user))
    logger.debug('message: {0}'.format(message))
    logger.debug('chat_node_pk: {0}'.format(chat_node_pk))
    logger.debug('bot_pk: {0}'.format(bot_pk))
    logger.debug('message_id: {0}'.format(message.message_id))

    logger.debug('message_date: {0}'.format(message.date))
    logger.debug('chat_id: {0}'.format(message.chat.id))
    logger.debug('user_id: {0}'.format(user.id))
    logger.debug('first_name: {0}'.format(user.first_name))

    username = getattr(user, 'username', None)
    # logger.debug('hasattr(user, "username"): {0}'.format(hasattr(user, 'username')))

    last_name = getattr(user, 'last_name', None)

    logger.debug('last_name: {0}'.format(last_name))
    logger.debug('username: {0}'.format(username))

    logger.debug('language_code: {0}'.format(user.language_code))

    history_item = ChatHistory.objects.create(
        chat_id=message.chat.id,
        user_id=user.id,
        first_name=message.chat.first_name,
        last_name=last_name,
        username=username,
        message_id=message.message_id,
        message_date=message.date,
        language_code=user.language_code,
        chat_node_id=chat_node_pk,
        bot_id=bot_pk,
    )

    logger.debug('history_item: {0}'.format(user.language_code))

    logger.debug('===== save_message_history: END =====')

    return history_item


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context, *args, **kwargs)

        return command_func

    return decorator

send_typing_action = send_action(ChatAction.TYPING)


@log_exception
def get_children_node_data(parent_node_pk):
    from chattree.models import ChatNode
    
    #if parent_node_pk == 82:
    #    return [{'answer': 'Есть РВП', 'pk':92}, {'answer': 'Есть ВНЭ', 'pk': 93}, ]
    #else:
    children_node_data = ChatNode.objects.filter(parent_id=parent_node_pk).values('answer', 'pk')
    # logger.debug('children_node_data: {0}'.format(children_node_data))

    return children_node_data


@log_exception
def get_keyboard_markup(children_node_data, bot_pk):
    """
    callback_data: <node_pk>&<bot_pk>
    :param children_node_data:
    :param bot_pk:
    :return:
    """
    keyboard = [[InlineKeyboardButton(d['answer'],
                                      callback_data='&'.join([str(d['pk']), str(bot_pk), ])), ]
                for d in children_node_data]

    # logger.debug('keyboard: {0}'.format(keyboard))

    return InlineKeyboardMarkup(keyboard)


@log_exception
def get_chat_node(node_pk):
    from chattree.models import ChatNode

    return ChatNode.objects.filter(pk=node_pk).values('question', 'answer', 'pk')


@log_exception
def get_chattree_bot(bot_token):
    from chattree.models import Bot

    bot = Bot.objects.filter(token=bot_token).values('start_message',
                                                     'end_message',
                                                     'chat_node__id',
                                                     'id')
    logger.debug('bot: {0}'.format(bot))
    assert bot, 'Cannot find chattree bot model for this token!'

    return bot[0]


@log_exception
@send_typing_action
def start(update, context):
    logger.debug('context.bot.token: {0}'.format(context.bot.token))

    chattree_bot = get_chattree_bot(context.bot.token)

    update.message.reply_text(chattree_bot['start_message'],
                              parse_mode='HTML',
                              disable_web_page_preview=True)

    user = update.message.from_user

    send_chat_node(chattree_bot['chat_node__id'],
                   update.message.chat_id, context, user, chattree_bot['id'])

start_handler = CommandHandler('start', start)


def end(chat_id, context, chat_node_pk, user, bot_pk):
    logger.debug('context.bot.token: {0}'.format(context.bot.token))
    chattree_bot = get_chattree_bot(context.bot.token)

    chat_history_url = 'https://{0}/c/{1}'.format(settings.HOST_NAME, chat_node_pk)

    message1 = context.bot.send_message(chat_id, '[История общения с ботом]({0})'.format(chat_history_url),
                                      parse_mode='Markdown',
                                      disable_web_page_preview=False, )

    save_message_history(user=user, message=message1, chat_node_pk=chat_node_pk, bot_pk=bot_pk)

    message2 = context.bot.send_message(chat_id, chattree_bot['end_message'],
                                      parse_mode='HTML',
                                      disable_web_page_preview=True, )
    save_message_history(user=user, message=message2, chat_node_pk=chat_node_pk, bot_pk=bot_pk)


@log_exception
def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())


@log_exception
def send_chat_node(chat_node_pk, chat_id, context, user, bot_pk):

    logger.debug('===== send_chat_node: START =====')

    logger.debug('chat_node_pk: {0}'.format(chat_node_pk))
    logger.debug('chat_id: {0}'.format(chat_id))
    logger.debug('context: {0}'.format(context))
    logger.debug('user: {0}'.format(user))
    logger.debug('bot_pk: {0}'.format(bot_pk))
    chat_node = get_chat_node(chat_node_pk)
    logger.debug(('chat_node: {0}'.format(chat_node)))

    logger.debug('===== send_chat_node: END =====')

    if chat_node:
        children_node_data = get_children_node_data(chat_node_pk)

        if len(children_node_data) > 1:  # If there are at least two children, display buttons
            logger.debug('len(children_node_data) > 1')
            reply_kb_markup = get_keyboard_markup(children_node_data, bot_pk)
            # update.message.reply_text('Thank you! I hope we can talk again some day.')
            message = context.bot.send_message(chat_id,
                                     chat_node[0]['question'],
                                     reply_markup=reply_kb_markup,
                                     parse_mode='HTML',
                                     disable_web_page_preview=True
                                     )
            save_message_history(user=user,
                                 message=message,
                                 chat_node_pk=chat_node[0]['pk'], bot_pk=bot_pk)

        elif len(children_node_data) == 0:  # If there are no children, display self
                                            #  and then display end message
            logger.debug('len(children_node_data) == 0')

            if chat_node[0]['question']:
                message = context.bot.send_message(chat_id, chat_node[0]['question'],
                                         parse_mode='HTML',
                                         disable_web_page_preview=True
                                         )
                save_message_history(user=user,
                                     message=message,
                                     chat_node_pk=chat_node[0]['pk'], bot_pk=bot_pk)
            end(chat_id, context, chat_node_pk, user, bot_pk)

        else:  # If there is only one child, display it without menu and then display child
            logger.debug('len(children_node_data) == 1')
            assert len(children_node_data) == 1, 'There must be only one child'

            if chat_node[0]['question']:
                message = context.bot.send_message(chat_id, chat_node[0]['question'],
                                         parse_mode='HTML',
                                         disable_web_page_preview=True
                                         )
                save_message_history(user=user, message=message,
                                     chat_node_pk=chat_node[0]['pk'], bot_pk=bot_pk)

            # send_chat_node(children_node_data[0]['pk'], chat_id, context)
            send_chat_node(children_node_data[0]['pk'], chat_id,
                           context, user, bot_pk)




@log_exception
@send_typing_action
def callback_answer(update, context):
    from chattree.models import ChatHistory
    query = update.callback_query
    # logger.debug('query.bot.base_url: {0}'.format(query.bot.base_url))
    logger.debug('query: {0}'.format(query))

    context.bot.answer_callback_query(
            query.id,
            # text='Hello! This callback: {0}'.format(query.data),
            # show_alert=True
            )

    chat_node_pk_str, bot_pk_str = query.data.split('&')
    user = query.from_user

    logger.debug('===== send_chat_node: START =====')

    logger.debug('query.data: {0}'.format(query.data))
    logger.debug('chat_node_pk_str: {0}'.format(chat_node_pk_str))
    logger.debug('user: {0}'.format(user))
    logger.debug('query.message.chat_id: {0}'.format(query.message.chat_id))
    logger.debug('bot_pk_str: {0}'.format(bot_pk_str))

    logger.debug('===== send_chat_node: END =====')

    message_id = query.message.message_id
    #If there are bot messages below this conversation, detete them:
    for history_message_id in ChatHistory.objects.filter(user_id=user.id, bot_id=bot_pk_str,
                                              chat_id=query.message.chat_id).filter(
        message_id__gt=message_id).values_list('message_id', flat=True):
        try:
            context.bot.delete_message(chat_id=query.message.chat_id, message_id=history_message_id)
        except TelegramError:
            pass

    send_chat_node(int(chat_node_pk_str), query.message.chat_id,
                   context, user, int(bot_pk_str))


@log_exception
def setup_bot(token):
    # Create bot, update queue and dispatcher instances
    bot = Bot(token)

    dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
    dispatcher.add_handler(CallbackQueryHandler(callback_answer, pass_user_data=True,
                                                                 pass_chat_data=True))
    dispatcher.add_handler(start_handler)

    return dispatcher

