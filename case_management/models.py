import os
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from case_management.enums import (
    OfficialIdentifiers,
    CaseStates,
    EmploymentStatus,
    Genders,
    MaritalStatuses,
    CivilMarriageTypes,
    Languages,
    Provinces,
    LogChangeTypes,
)
from django_countries.fields import CountryField
from django.conf import settings
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from case_management.managers import UserManager
from django_lifecycle import LifecycleModel, hook, AFTER_CREATE, AFTER_UPDATE, BEFORE_DELETE
from django.apps import apps


LOG_CHANGE_EXCLUDED_FIELDS = ('id', 'created_at', 'updated_at')


class User(AbstractUser):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False, blank=True, default="")
    membership_number = models.CharField(max_length=20, null=False, blank=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    contact_number = PhoneNumberField(null=False, blank=True, default="")
    case_office = models.ForeignKey(
        'CaseOffice',
        related_name='users',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    username = None
    first_name = None
    last_name = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_module_perms(self, app_label):
        return self.is_superuser

    def has_perm(self, perm, obj=None):
        return self.is_superuser


class Log(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    parent_id = models.IntegerField(null=False, blank=False)
    parent_type = models.CharField(
        max_length=255, null=False, blank=False, default='LegalCase'
    )

    target_id = models.IntegerField(null=False, blank=False)
    target_type = models.CharField(max_length=255, null=False, blank=False)

    action = models.CharField(max_length=255, null=False, blank=False)
    user = models.ForeignKey(
        User, related_name='logs', null=True, on_delete=models.CASCADE
    )

    note = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f'{self.action} - {self.target_type}'

    @property
    def extra(self):
        info = {'user': {'name': self.user.name}}
        return info


class LogChange(models.Model):
    id = models.AutoField(primary_key=True)
    log = models.ForeignKey(Log, related_name='changes', on_delete=models.CASCADE)

    field = models.CharField(max_length=255)
    value = models.TextField(null=True)
    action = models.CharField(max_length=10, choices=LogChangeTypes.choices)


def _logChange(log_id, field, value, action):
    log_change = LogChange(
        log=log_id, field=field, value=value, action=action
    )
    log_change.save()


def logIt(self, action, parent_id=None, parent_type=None, user=None, note=None):
    target_type = self.__class__.__name__
    target_id = self.id

    if parent_id is None:
        parent_id = self.id

    if parent_type is None:
        parent_type = self.__class__.__name__

    if note is None:
        target_model = apps.get_model('case_management', target_type)
        record = target_model.objects.filter(id=target_id)
        if record.count() > 0:
            note = record[0].__str__()
        else:
            note = target_type

    self.log = Log(
        parent_id=parent_id,
        parent_type=parent_type,
        target_id=target_id,
        target_type=target_type,
        action=action,
        user=user,
        note=note,
    )
    self.log.save()
    for field in self._meta.get_fields():
        value = getattr(self, field.name)
        if field.name not in LOG_CHANGE_EXCLUDED_FIELDS and (
            action == 'Create' or self.has_changed(field.name)
        ):
            _logChange(self.log, field.name, value, LogChangeTypes.CHANGE)


@receiver(m2m_changed)
def logManyToManyChange(
    sender, instance=None, action=None, model=None, pk_set=None, **kwargs
):
    if action in ('post_add', 'post_remove'):
        if action == 'post_add':
            change_action = LogChangeTypes.ADD
        elif action == 'post_remove':
            change_action = LogChangeTypes.REMOVE
        _, field = sender.__name__.split('_', 1)
        value = list(pk_set)
        _logChange(instance.log, field, value, change_action)


class LoggedModel(LifecycleModel, models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, related_name='+', on_delete=models.CASCADE, null=True, editable=False
    )
    updated_by = models.ForeignKey(
        User, related_name='+', on_delete=models.CASCADE, null=True, editable=False
    )

    @hook(AFTER_CREATE)
    def log_create(self):
        logIt(self, 'Create', user=self.created_by)

    @hook(AFTER_UPDATE)
    def log_update(self):
        logIt(self, 'Update', user=self.updated_by)

    class Meta:
        abstract = True


class CaseOffice(LoggedModel):
    name = models.CharField(max_length=500, unique=True)
    description = models.TextField()
    case_office_code = models.CharField(max_length=3, default="D00")

    def __str__(self):
        return self.name


class CaseType(LoggedModel):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Client(LoggedModel):
    name = models.CharField(max_length=255, null=False, blank=False)
    preferred_name = models.CharField(max_length=128, blank=True)
    official_identifier = models.CharField(max_length=64, null=True, blank=True)
    official_identifier_type = models.CharField(
        max_length=25, choices=OfficialIdentifiers.choices, null=True, blank=True
    )
    date_of_birth = models.DateTimeField(null=True, blank=True)
    contact_number = PhoneNumberField(blank=True)
    alternative_contact_number = PhoneNumberField(blank=True)
    contact_email = models.EmailField(max_length=254, blank=True)
    alternative_contact_email = models.EmailField(max_length=254, blank=True)
    address = models.CharField(max_length=255, blank=True)
    province = models.CharField(max_length=20, blank=True, choices=Provinces.choices)
    gender = models.CharField(max_length=20, blank=True, choices=Genders.choices)
    marital_status = models.CharField(
        max_length=20, blank=True, choices=MaritalStatuses.choices
    )
    civil_marriage_type = models.CharField(
        max_length=25, blank=True, choices=CivilMarriageTypes.choices
    )
    dependents = models.IntegerField(
        validators=[MinValueValidator(0)], blank=True, null=True
    )
    next_of_kin_name = models.CharField(max_length=255, blank=True)
    next_of_kin_relationship = models.CharField(max_length=255, blank=True)
    next_of_kin_contact_number = PhoneNumberField(blank=True)
    home_language = models.CharField(
        max_length=20, blank=True, choices=Languages.choices
    )
    translator_needed = models.BooleanField(blank=True, null=True)
    translator_language = models.CharField(
        max_length=20, blank=True, choices=Languages.choices
    )
    nationality = CountryField(blank=True)
    employment_status = models.CharField(
        max_length=25, blank=True, choices=EmploymentStatus.choices
    )
    has_disability = models.BooleanField(blank=True, null=True)
    disabilities = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self.preferred_name == '':
            self.preferred_name = self.name
        super().save(*args, **kwargs)

    class Meta:
        unique_together = [['official_identifier', 'official_identifier_type']]

    def __str__(self):
        return self.preferred_name

    @property
    def updates(self):
        '''TODO: Do this in scalable way e.g. in view using proper join
        The below would not scale, because the request is done for each row
        '''
        updates = Log.objects.filter(target_type='Client', target_id=self.id).order_by(
            '-updated_at'
        )
        return updates


class LegalCase(LoggedModel):
    case_number = models.CharField(max_length=32, null=False, blank=False, unique=True)
    state = models.CharField(
        max_length=10, choices=CaseStates.choices, default=CaseStates.OPENED
    )
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    client = models.ForeignKey(
        Client, related_name='legal_cases', on_delete=models.CASCADE
    )
    case_types = models.ManyToManyField(CaseType, blank=True)
    case_offices = models.ManyToManyField(CaseOffice)

    summary = models.TextField(null=False, blank=True, default="")
    referred_by = models.CharField(max_length=255, blank=True)
    has_respondent = models.BooleanField(blank=True, null=True)
    respondent_name = models.CharField(max_length=255, blank=True)
    respondent_contact_number = PhoneNumberField(blank=True)

    def __str__(self):
        return self.case_number


class Meeting(LoggedModel):
    legal_case = models.ForeignKey(
        LegalCase, related_name='meetings', on_delete=models.CASCADE
    )
    location = models.CharField(max_length=255, null=False, blank=False)
    meeting_type = models.CharField(
        max_length=50, null=False, blank=False, default="In person meeting"
    )
    meeting_date = models.DateTimeField(null=False, blank=False)
    notes = models.TextField(null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=True, default="")
    legal_case_file = models.ForeignKey(
        'LegalCaseFile',
        related_name='legal_case_files',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    @hook(AFTER_CREATE)
    def log_create(self):
        logIt(self, 'Create', user=self.created_by, parent_id=self.legal_case.id, parent_type='LegalCase')

    @hook(AFTER_UPDATE)
    def log_update(self):
        logIt(self, 'Update', user=self.updated_by, parent_id=self.legal_case.id, parent_type='LegalCase')

    @hook(BEFORE_DELETE)
    def log_delete(self):
        logIt(self, 'Delete', user=self.updated_by, parent_id=self.legal_case.id, parent_type='LegalCase')

    def __str__(self):
        return self.name


class LegalCaseFile(LoggedModel):
    legal_case = models.ForeignKey(
        LegalCase, related_name='files', on_delete=models.CASCADE
    )
    upload = models.FileField(upload_to='uploads/')
    description = models.CharField(max_length=255, null=False, blank=True, default='')

    def save(self, *args, **kwargs):
        if self.description == '':
            self.description = self.upload_file_name()
        super().save(*args, **kwargs)

    @hook(AFTER_CREATE)
    def log_create(self):
        logIt(self, 'Create', user=self.created_by, parent_id=self.legal_case.id, parent_type='LegalCase')

    @hook(AFTER_UPDATE)
    def log_update(self):
        logIt(self, 'Update', user=self.updated_by, parent_id=self.legal_case.id, parent_type='LegalCase')

    def __str__(self):
        return self.upload_file_name()

    def upload_file_extension(self):
        return os.path.splitext(self.upload.file.name)[1][1:]

    def upload_file_name(self):
        return os.path.basename(self.upload.file.name)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
