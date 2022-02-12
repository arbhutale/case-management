from rest_framework import serializers
from django_countries.serializers import CountryFieldMixin
from case_management.models import (
    CaseOffice,
    CaseType,
    Client,
    LegalCase,
    CaseUpdate,
    File,
    Meeting,
    Note,
    User,
    Log,
    LogChange,
)
from case_management.enums import MaritalStatuses


class LogChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogChange
        fields = '__all__'


class LogSerializer(serializers.ModelSerializer):
    changes = LogChangeSerializer(many=True, read_only=True)
    extra = serializers.ReadOnlyField()

    class Meta:
        model = Log
        fields = '__all__'


class CaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseType
        fields = '__all__'


class LegalCaseSerializer(serializers.ModelSerializer):
    meetings = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    case_number = serializers.CharField(required=False)

    def validate(self, data):
        if data.get('has_respondent') and not data.get('respondent_name'):
            raise serializers.ValidationError(
                {
                    'respondent_name': 'respondent_name is mandatory if has_respondent is true'
                }
            )
        return data

    class Meta:
        model = LegalCase
        fields = '__all__'


class ClientSerializer(CountryFieldMixin, serializers.ModelSerializer):
    legal_cases = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    updates = LogSerializer(many=True, read_only=True)

    def validate(self, data):
        if data.get('official_identifier') and not data.get('official_identifier_type'):
            raise serializers.ValidationError(
                {
                    'official_identifier_type': 'official_identifier_type is mandatory if official_identifier is provided'
                }
            )
        if data.get('translator_needed') and not data.get('translator_language'):
            raise serializers.ValidationError(
                {
                    'translator_language': 'translator_language is mandatory if translator_needed is true'
                }
            )
        if data.get(
            'marital_status'
        ) == MaritalStatuses.CIVIL_MARRIAGE and not data.get('civil_marriage_type'):
            raise serializers.ValidationError(
                {
                    'civil_marriage_type': f'civil_marriage_type is mandatory if marital_status is {MaritalStatuses.CIVIL_MARRIAGE}'
                }
            )
        if data.get('has_disability') and not data.get('disabilities'):
            raise serializers.ValidationError(
                {'disabilities': f'disabilities is mandatory if has_disability is true'}
            )
        return data

    class Meta:
        model = Client
        fields = '__all__'
        depth = 1


class CaseOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseOffice
        fields = '__all__'


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            'id',
            'legal_case',
            'upload',
            'upload_file_name',
            'upload_file_extension',
            'description',
            'created_at',
            'updated_at',
        ]


class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = '__all__'


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = '__all__'


class CaseUpdateSerializer(serializers.ModelSerializer):
    files = serializers.PrimaryKeyRelatedField(
        many=True, read_only=False, queryset=File.objects.all(), required=False
    )
    meeting = MeetingSerializer(many=False, read_only=False, required=False)
    note = NoteSerializer(many=False, read_only=False, required=False)
    update_types_list = ('files', 'meeting', 'notes')
    nested_update_types = {
        'files': {'action': 'assign'},
        'meeting': {'action': 'create', 'model': Meeting},
        'note': {'action': 'create', 'model': Note},
    }

    def validate(self, data):
        update_type_count = 0
        for update_type in self.update_types_list:
            update_type_count += update_type in data
        if update_type_count == 0:
            raise serializers.ValidationError(
                f'Provide one of {self.update_types_list}'
            )
        if update_type_count > 1:
            raise serializers.ValidationError(
                f'Provide only one of {self.update_types_list}'
            )
        return data

    def create(self, validated_data):
        for update_type, update_type_details in self.nested_update_types.items():
            if update_type in validated_data:
                update_type_details['data'] = validated_data.pop(update_type)
        case_update = CaseUpdate.objects.create(**validated_data)
        for update_type_name, update_type_details in self.nested_update_types.items():
            if 'data' in update_type_details:
                if update_type_details['action'] == 'create':
                    update_type_details['model'].objects.create(
                        **update_type_details['data'], case_update=case_update
                    )
                elif update_type_details['action'] == 'assign':
                    getattr(case_update, update_type_name).set(
                        update_type_details['data']
                    )
                else:
                    raise Exception('Unknown case update action')
        return case_update

    class Meta:
        model = CaseUpdate
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'contact_number',
            'email',
            'membership_number',
            'case_office',
        ]
