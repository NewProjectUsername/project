from django.db import models
from django.contrib.auth import get_user_model
#from django.contrib.auth.models import User
#from Landing.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from django.utils.encoding import python_2_unicode_compatible
from django_countries import Countries
from django_countries.fields import CountryField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings
from Event.models import Event, Lecture
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
#import Event

#User = get_user_model()


# Create your models here.
GENDERS = (
        ('M', _('Male')),
        ('W', _('Female'))
    )

class Timestampable(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    created_at = AutoCreatedField(_('creation time'))
    updated_at = AutoLastModifiedField(_('last modification time'))

    class Meta:
        abstract = True


class Profile(models.Model):
    """User profile, basic info that is given at registration. Probably
    not mandatory.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    #name = models.CharField(max_length=256, blank=True, null=True)
    #surname = models.CharField(max_length=256, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDERS, blank=True, null=True)
    birth_year = models.IntegerField(blank=True,
                                     null=True,
                                     validators=[MaxValueValidator(2015),
                                                 MinValueValidator(1920)])

    # -- I imagined these (below) are optional, but should they be present
    #     they can be filled-out automatically when registering for events.
    address = models.CharField(max_length=256, blank=True, null=True)
    city = models.CharField(max_length=256, blank=True, null=True)
    post = models.CharField(max_length=256, blank=True, null=True)
    country = CountryField(blank_label='(select country)', blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        """String representation ..."""
        return '{}, {} ({})'.format(self.user.first_name, self.user.last_name,
                                    self.user.username)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

DEFAULT_EXAM_ID = 1
class EventProfile(Timestampable, models.Model):
    """User info for an Event. Also shows who is registered at the
    specific Event.

    Fields like name, surname, birth_year and gender are left out,
    because they should be the same for one user across events.

    By default a user entered in this table is a visitor, not
    companion, but it can be both, based on the Boolean field.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='profiles')
    event = models.ForeignKey(Event, related_name="profiles")

    name = models.CharField(max_length=256, blank=True, null=True)
    surname = models.CharField(max_length=256, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDERS, blank=True, null=True)
    email = models.EmailField(max_length=256, blank=True, null=True)
    # birth_year = models.IntegerField(blank=True,
    #                                null=True,
    #                                validators=[MaxValueValidator(2015),
    #                                            MinValueValidator(1920)])
    birth_year = models.DateTimeField(blank=True, null=True)
    address = models.CharField(max_length=256, blank=True, null=True)
    city = models.CharField(max_length=256, blank=True, null=True)
    post = models.CharField(max_length=256, blank=True, null=True)
    country = CountryField(blank_label='(select country)', blank=True, null=True)
    dinner = models.BooleanField(default=False)
    nutrition = models.CharField(max_length=32, blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    company_invoice = models.BooleanField(default=False)
    company_name = models.CharField(max_length=256, blank=True, null=True)
    company_address = models.CharField(max_length=256, blank=True, null=True)
    tax_number = models.IntegerField(blank=True, null=True)
    company_email = models.EmailField(max_length=256, blank=True, null=True)
    network_visible = models.BooleanField(default=False)
    for_pay = models.FloatField(default=0)
    payed = models.BooleanField(default=False)
    is_upn = models.BooleanField(default=False)
    pay_details = models.TextField(max_length=2048, blank=True, null=True)
    upn_reference = models.IntegerField(blank=True, null=True)
    is_finished = models.BooleanField(default=False)
    is_companion = models.BooleanField(default=False)
    days_on_event = models.IntegerField(default=0, blank=True, null=True)
    idnumber = models.IntegerField(default=0)

    soft = models.BooleanField(default=False)
    note = models.CharField(max_length=1024, blank=True, null=True)
    date_of_registration = models.DateTimeField(auto_now_add=True)

    uhf_id = models.CharField(max_length=128, blank=True, null=True, default=0)
    nfc_id = models.CharField(max_length=128, blank=True, null=True, default=0)
    barcode_no = models.CharField(max_length=128, blank=True, null=True)

    lectures = models.ManyToManyField(Lecture)
    confirmation = models.BooleanField(default=False)
    registration_step_finished = models.IntegerField(default=0)

    def __str__(self):
        return self.name+" "+self.surname
