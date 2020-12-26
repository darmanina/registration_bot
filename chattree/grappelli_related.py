from grappelli.settings import AUTOCOMPLETE_LIMIT
from grappelli.views.related import AutocompleteLookup, RelatedLookup, get_label, get_label_safe
from django.apps import apps


class ChatNodeRelatedMixin(object):
    def request_is_valid(self):
        return True
        return 'object_id' in self.GET and 'app_label' in self.GET and 'model_name' in self.GET

    def get_model(self):
        try:
            self.model = apps.get_model(self.GET['app_label'], self.GET['model_name'])
        except LookupError:
            self.model = apps.get_model('chattree', 'ChatNode')
        return self.model

    def get_return_value(self, obj, obj_id):
        to_field = 'id'
        if to_field is not None:
            return_value = getattr(obj, to_field)
            if not isinstance(return_value, str) and not isinstance(return_value, int):
                return_value = obj.pk
            return return_value
        return obj_id

    def get_filtered_queryset(self, qs):
        filters = {}
        query_string = self.GET.get('query_string', None)
        # app_label = chattree & model_name = chatnode & query_string = _to_field = id & to_field = id
        # if query_string:
        #     for item in query_string.split(":"):
        #         k, v = item.split("=")
        #         if k != "_to_field":
        #             filters[smart_str(k)] = prepare_lookup_value(smart_str(k), smart_str(v))
        return qs.filter(**filters)

    # def get_data(self):
    #     return [{"value": self.get_return_value(f, f.pk), "label": 'chattree'} for f in self.get_queryset()[:AUTOCOMPLETE_LIMIT]]


class CustomRelatedLookup(ChatNodeRelatedMixin, RelatedLookup):
    def get_data(self):
        obj_id = self.GET['object_id']
        to_field = 'id'
        data = []
        if obj_id:
            try:
                if to_field is not None:
                    obj = self.get_queryset().get(**{to_field: obj_id})
                else:
                    obj = self.get_queryset().get(pk=obj_id)
                data.append({"value": "%s" % self.get_return_value(obj, obj_id), "label": get_label(obj), "safe": get_label_safe(obj)})
            except (self.model.DoesNotExist, ValueError):
                data.append({"value": obj_id, "label": _("?"), "safe": False})
        return data


class CustomAutocompleteLookup(ChatNodeRelatedMixin, AutocompleteLookup):
    pass
