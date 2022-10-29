import re
import pyotp
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.core.exceptions import ValidationError
from users.models import User, AuthOtp


@receiver(pre_save, sender=AuthOtp)
def generate_otp_key(sender, instance: AuthOtp, **kwargs):
    regex = re.match(r'^(010|070)-\d{3,4}-\d{4}$', instance.number)
    assert regex
    instance.otp_key = pyotp.random_base32()


@receiver(pre_save, sender=User)
def authenticate_user_phone(sender, instance: User, **kwargs):
    try:
        auth_otp = AuthOtp.objects.filter(number=instance.phone_number).latest()
    except AuthOtp.DoesNotExist:
        raise ValidationError('invalid_number')
    if not auth_otp.otp_register_code:
        raise ValidationError('unauthenticated_otp_code')
    if auth_otp.otp_register_code != instance.otp_register_code:
        raise ValidationError('invalid_otp_code')
