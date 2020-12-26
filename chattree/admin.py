from django.conf.urls import url
from django.contrib import admin
from django import forms
from django.contrib import messages
from django.utils.safestring import mark_safe
from django_mptt_admin.admin import DjangoMpttAdmin
from chattree.models import ChatNode, Bot
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.contrib.admin import helpers

from chattree.forms import ChatNodeCopyForm


class ChatNodeInlineAdmin(admin.StackedInline):
    model = ChatNode
    classes = ('grp-collapse grp-open',)

    extra = 0
    # def get_formset(self, request, obj=None, **kwargs):
    #     kwargs['exclude'] = ['question', ]
    #
    #     return super(ChatNodeInlineAdmin, self).get_formset(request, obj, **kwargs)

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(ChatNodeInlineAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'question':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        return formfield

class BotAdmin(admin.ModelAdmin):
    fieldsets = (
        ('', {
            'fields': ('name', 'start_message', 'end_message', ),
        }),
        ('Дополнительно', {
            'classes': ('grp-collapse grp-closed',),
            'fields' : ('chat_node', 'token', ),
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "chat_node":
            # This next line only shows owned objects
            # but you can write your own query!
            kwargs["queryset"] = db_field.related_model.objects.filter(parent__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ChatNodeAdmin(DjangoMpttAdmin):
    search_fields = ('question', 'answer', 'pk')

    raw_id_fields = ('parent',)
    autocomplete_lookup_fields = {
        'fk': ['parent', ],
    }

    inlines = [ChatNodeInlineAdmin, ]

    change_form_template = 'chatnode_change_form.html'

    def get_form(self, request, obj=None, **kwargs):
        # self.readonly_fields = ['parent', ]
        if hasattr(obj, 'state'):
            self.exclude = list()
            if not obj._state.adding:
                pass
        else:
            self.exclude = ('answer', )

        form = super(DjangoMpttAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(ChatNodeAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'question':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        return formfield	

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_add_another'] = False
        return super(ChatNodeAdmin, self).change_view(request, object_id,
            form_url, extra_context=extra_context)

    def copy_view(
            self,
            request,
            pk,
            # action_form,
            # action_title
    ):

        node = self.get_object(request, pk)

        if request.method == 'POST':
            form = ChatNodeCopyForm(request.POST, node_to_copy=node)
            if form.is_valid():
                count = form.save(node, request.user)
                if count > 0:
                    self.message_user(request, 'Поздравляем, копирование произведено успешно!'
                                               ' Дерево расжирело на {0}!'.format(count), level=messages.SUCCESS)
                else:
                    self.message_user(request, 'Ой, ничего не было скопировано, поскольку'
                                               ' вы попытались скопировать потомков ветки,'
                                               ' у которой их нет!',
                                      level=messages.WARNING, )
                url = reverse(
                    'admin:chattree_chatnode_changelist',

                    current_app=self.admin_site.name,
                )
                return HttpResponseRedirect(url)
        else:
            form = ChatNodeCopyForm(node_to_copy=node)

        # if True:
            # form = action_form()

            # node = ChatNode.objects.get(pk=pk)


        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['add'] = False
        context['change'] = True
        context['save_as'] = False
        context['has_add_permission'] = True
        context['has_change_permission'] = True
        context['has_view_permission'] = True
        context['has_editable_inline_admin_formsets'] = False
        context['has_delete_permission'] = False
        context['show_save_and_add_another'] = False
        context['show_save_and_continue'] = False

        context['original'] = node
        # context['account'] = account
        context['title'] = mark_safe('Копирование ветки <a href="{0}">{1}</a>'.format(
            reverse('admin:chattree_chatnode_change', args=[node.pk, ]), node, ))

        form = helpers.AdminForm(
            form=form,
            fieldsets=(
                ('', {
                    'fields': ('parent', 'include_first_node'),
                }),),
            # Clear prepopulated fields on a view-only form to avoid a crash.
            prepopulated_fields={},
            readonly_fields=[],
            model_admin=self)

        context['form'] = form
        context['adminform'] = form

        return TemplateResponse(
            request,
            'chatnode_copy_form.html',
            # 'admin/account/account_action.html',
            context,
        )
        # else:
        #     form = ChatNodeCopyForm(request.POST, node_to_copy=node)
        #     if form.is_valid():
        #         count = form.save(node, request.user)
        #         if count > 0:
        #             self.message_user(request, 'Копирование произведено успешно! Дерево расжирело на {0} элементов!'.format(count), level=messages.SUCCESS)
        #         else:
        #             self.message_user(request, 'Ничего не было скопировано, поскольку'
        #                                        ' вы попытались скопировать потомков ветки,'
        #                                        ' у которой их нет!',
        #                               level=messages.WARNING, )
        #         url = reverse(
        #             'admin:chattree_chatnode_changelist',
        #
        #             current_app=self.admin_site.name,
        #         )
        #         return HttpResponseRedirect(url)
        #     else:
        #
        #         form = ChatNodeCopyForm(node_to_copy=node)
        #         context = self.admin_site.each_context(request)
        #         context['opts'] = self.model._meta
        #         context['add'] = False
        #         context['change'] = True
        #         context['save_as'] = False
        #         context['has_add_permission'] = True
        #         context['has_change_permission'] = True
        #         context['has_view_permission'] = True
        #         context['has_editable_inline_admin_formsets'] = False
        #         context['has_delete_permission'] = False
        #         context['show_save_and_add_another'] = False
        #         context['show_save_and_continue'] = False
        #
        #         context['original'] = node
        #         # context['account'] = account
        #         context['title'] = mark_safe('Копирование ветки <a href="{0}">{1}</a>'.format(
        #             reverse('admin:chattree_chatnode_change', args=[node.pk, ]), node, ))
        #
        #         form = helpers.AdminForm(
        #             form=form,
        #             fieldsets=(
        #                 ('', {
        #                     'fields': ('parent', 'include_first_node'),
        #                 }),),
        #             # Clear prepopulated fields on a view-only form to avoid a crash.
        #             prepopulated_fields={},
        #             readonly_fields=[],
        #             model_admin=self)
        #
        #         context['form'] = form
        #         context['adminform'] = form
        #
        #         return TemplateResponse(
        #             request,
        #             'chatnode_copy_form.html',
        #             # 'admin/account/account_action.html',
        #             context,
        #         )


        # return ChatNodeDetailView.as_view(request, my_id, self)
    def get_urls(self):
        urls = super(ChatNodeAdmin, self).get_urls()
        my_urls = [
            url(r'^(?P<pk>\d+)/copy/$', self.admin_site.admin_view(self.copy_view), name='copy_view')
        ]
        return my_urls + urls

admin.site.register(ChatNode, ChatNodeAdmin)
admin.site.register(Bot, BotAdmin)
