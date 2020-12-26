from django import forms

from chattree.models import ChatNode
from django.forms import ModelChoiceField, BooleanField, CharField


# class ChatNodeMoveForm(MoveNodeForm):
#
#     class Meta:
#         model = ChatNode
#         fields = ['target', 'position']

# "http://127.0.0.1:8000/grappelli/lookup/autocomplete/?term=%D0%9F%D1%80%D0%B8&app_label=chattree&model_name=chatnode&query_string=_to_field=id&to_field=id"

def copy_node(instance, target_parent):

    new_instance = ChatNode.objects.create(
        parent=target_parent,
        answer=instance.answer,
        question=instance.question)

    return new_instance


def copy_children(source_branch, target_parent, exclude_pks=None, count=0):
    if exclude_pks is None:
        exclude_pks = [target_parent.pk, ]

    for child in source_branch.get_children():
        # Make children of `plan` node
        if child.pk not in exclude_pks:
            new_child = copy_node(child, target_parent=target_parent)
            count += 1
            exclude_pks.append(new_child.pk)
            count += copy_children(child, target_parent=new_child,
                                   exclude_pks=exclude_pks)
    return count


class ChatNodeCopyForm(forms.ModelForm):
    node_to_copy = None

    parent = CharField(
                              widget=forms.TextInput(
                                  attrs={
                                  'class': "vForeignKeyRawIdAdminField", }
                              ),
                              label='Куда копировать',
                              help_text='Введите номер или фрагмент текста'
                                        ' корневого вопроса интересующей вас ветки')

    include_first_node = BooleanField(
        label='Включая родительский вопрос',
        help_text='Отметьте галочкой только если хотите скопировать ветку'
                  ' вместе с её родительским вопросом.', required=False)

    def __init__(self, *args, **kwargs):

        self.node_to_copy = kwargs.pop('node_to_copy')

        # if args is not None:
        #     self.parent_field = self.base_fields['parent']
        #     del self.base_fields['parent']  # Do not validate parent
        # if post_data and post_files:
        #     self.base_fields.remove(field_name)

        super(ChatNodeCopyForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = dict()

        if 'parent' in self.data:
            try:
                parent = ChatNode.objects.get(pk=int(self.data['parent']))
            except ChatNode.DoesNotExist:
                self.add_error('parent', 'Выбранная ветка не существует!')
            else:
                cleaned_data.update({'parent': parent})

        else:
            self.add_error('parent', 'Вы не выбрали ветку для копирования!')

        if 'include_first_node' in self.data:
            cleaned_data.update({'include_first_node': self.data['include_first_node']})
        else:
            cleaned_data.update({'include_first_node': False })

        return cleaned_data

    def save(self, commit=True, request=None, *args, **kwargs):
        count = 0
        if self.cleaned_data['include_first_node']:
            target = copy_node(self.node_to_copy, self.cleaned_data['parent'])
            count += 1
        else:
            target = self.cleaned_data['parent']

        count += copy_children(self.node_to_copy, target)

        return count

    class Meta:
        model = ChatNode
        fields = ['parent']




