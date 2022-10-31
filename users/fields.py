from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class ChoiceTypeField(serializers.ChoiceField):
    def __init__(self, valid_choice=None, **kwargs):
        super().__init__(**kwargs)
        self.valid_choice = valid_choice

    def fail(self, key, **kwargs):
        msg = self.error_messages.get(key, None)
        message_string = msg.format(**kwargs)
        detail = {"detail": message_string}
        detail.update(self.valid_choice)
        raise ValidationError(detail, code=key)

    default_error_messages = {
        'invalid_choice': "invalid_choice_{input}",
    }
