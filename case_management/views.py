import re
from datetime import date, timedelta
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins
from rest_framework.parsers import MultiPartParser, FormParser

from django.views import generic

from django.db import connection

from django.http import HttpResponseBadRequest

from case_management.serializers import (
    CaseOfficeSerializer,
    CaseTypeSerializer,
    ClientSerializer,
    LegalCaseSerializer,
    MeetingSerializer,
    UserSerializer,
    LogSerializer,
    LegalCaseFileSerializer,
)
from case_management.models import (
    CaseOffice,
    CaseType,
    Client,
    LegalCase,
    Meeting,
    User,
    Log,
    LegalCaseFile,
)

import time


class UpdateRetrieveViewSet(
    mixins.UpdateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    A viewset that provides just the `update', and `retrieve` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """

    pass


class CreateListRetrieveViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset that provides just the `create', 'list', and `retrieve` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """

    pass


class Index(generic.TemplateView):
    template_name = "index.html"


class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {
                'token': token.key,
                'user_id': user.pk,
            }
        )


class CaseOfficeViewSet(viewsets.ModelViewSet):
    queryset = CaseOffice.objects.all()
    serializer_class = CaseOfficeSerializer


class CaseTypeViewSet(viewsets.ModelViewSet):
    queryset = CaseType.objects.all()
    serializer_class = CaseTypeSerializer


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer

    def get_queryset(self):
        queryset = Client.objects.all()
        case_office = self.request.query_params.get('caseOffice')
        if case_office is not None:
            queryset = Client.objects.filter(legal_cases__case_offices__id=case_office).distinct('id')
        return queryset

class LegalCaseViewSet(viewsets.ModelViewSet):
    queryset = LegalCase.objects.all()
    serializer_class = LegalCaseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client']

    def perform_create(self, serializer):
        try:
            next_id = LegalCase.objects.latest('id').id + 1
        except LegalCase.DoesNotExist:
            next_id = 1
        case_office = CaseOffice.objects.get(pk=self.request.data['case_offices'][0])
        case_office_code = case_office.case_office_code
        generated_case_number = (
            f'{case_office_code}/{time.strftime("%y%m")}/{str(next_id).zfill(4)}'
        )
        serializer.save(case_number=generated_case_number)


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['legal_case']


class UserViewSet(UpdateRetrieveViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class LogViewSet(CreateListRetrieveViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['parent_id', 'parent_type', 'target_id', 'target_type']


class LegalCaseFileViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser)
    queryset = LegalCaseFile.objects.all()
    serializer_class = LegalCaseFileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['legal_case']


def _get_summary_months_range(request):
    months = {'start': None, 'end': None}
    month_input_pattern = re.compile('^([0-9]{4})-(0[1-9]|1[0-2])$')
    for month in list(months):
        query_param = f'{month}Month'
        query_param_input = request.query_params.get(query_param, None)
        if query_param_input is not None:
            match = month_input_pattern.match(query_param_input)
            if match:
                year_input = int(match.group(1))
                month_input = int(match.group(2))
                months[month] = date(year=year_input, month=month_input, day=1)
            else:
                return HttpResponseBadRequest(
                    f'{query_param} query param must be in format yyyy-mm'
                )
    if months['end'] is None:
        if months['start'] is None:
            months['end'] = date.today()
        else:
            months['end'] = (months['start'] + timedelta(days=30 * 11.5)).replace(day=1)
    if months['start'] is None:
        months['start'] = (months['end'] - timedelta(days=30 * 10.5)).replace(day=1)
    start_month = months['start'].strftime("%Y-%m-%d")
    end_month = months['end'].strftime("%Y-%m-%d")
    return start_month, end_month


@api_view(['GET'])
def daily_summary(request):
    start_month, end_month = _get_summary_months_range(request)
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
WITH
	months AS (
		SELECT DATE_TRUNC('month', months_series)::date AS month, (DATE_TRUNC('month', months_series) + interval '1 month' - interval '1 day')::date month_end
		FROM generate_series(
			'{start_month}'::timestamp,
			'{end_month}'::timestamp,
			'1 month'::interval
		) months_series
	),
	days AS (
		SELECT DATE_TRUNC('day', days_series)::date AS day
		FROM generate_series(
			'2021-01-01'::timestamp,
			'2021-12-31'::timestamp,
			'1 day'::interval
		) days_series
	),
	metric_cases_created AS (
		SELECT case_office.caseoffice_id, DATE_TRUNC('month', legalcase.created_at)::date AS month, DATE_TRUNC('day', legalcase.created_at)::date AS day, COUNT(legalcase.id) n
		FROM case_management_legalcase legalcase, case_management_legalcase_case_offices case_office
		WHERE legalcase.id = case_office.legalcase_id
		GROUP BY month, case_office.caseoffice_id, day
	),
	metric_cases_closed AS (
		SELECT case_office.caseoffice_id, DATE_TRUNC('month', legalcase.created_at)::date AS month, DATE_TRUNC('day', log.created_at)::date AS day, COUNT(logchange.id) n
		FROM case_management_logchange logchange
		INNER JOIN case_management_log log ON log.id = logchange.log_id
		INNER JOIN case_management_legalcase legalcase ON legalcase.id = log.target_id
		INNER JOIN case_management_legalcase_case_offices case_office ON case_office.legalcase_id = legalcase.id
		WHERE logchange.field = 'state' AND logchange.value = 'Closed'
		GROUP BY month, case_office.caseoffice_id, day
	),
	metric_updates AS (
		SELECT case_office.caseoffice_id, DATE_TRUNC('month', legalcase.created_at)::date AS month, DATE_TRUNC('day', log.created_at)::date AS day, COUNT(log.id) n
		FROM case_management_log log
		INNER JOIN case_management_legalcase legalcase ON legalcase.id = log.target_id
		INNER JOIN case_management_legalcase_case_offices case_office ON case_office.legalcase_id = legalcase.id
		GROUP BY month, case_office.caseoffice_id, day
	)
SELECT json_object_agg(
  name, json_build_object(
    'Cases opened', (
		SELECT json_object_agg(
			to_char(months.month, 'YYYY-MM'), (
				SELECT json_agg(
			  		json_build_object(
						'date', days.day,
						'value', (
				  			SELECT n
				  			FROM metric_cases_created cases_created
				  			WHERE cases_created.caseoffice_id = caseoffice.id AND cases_created.day = days.day
						)
			  		)
				)
				FROM days
				WHERE days.day BETWEEN months.month and months.month_end
			)
		)
		FROM months
	),
	'Cases closed', (
		SELECT json_object_agg(
			to_char(months.month, 'YYYY-MM'), (
				SELECT json_agg(
			  		json_build_object(
						'date', days.day,
						'value', (
				  			SELECT n
				  			FROM metric_cases_closed cases_closed
				  			WHERE cases_closed.caseoffice_id = caseoffice.id AND cases_closed.day = days.day
						)
			  		)
				)
				FROM days
				WHERE days.day BETWEEN months.month and months.month_end
			)
		)
		FROM months
	),
	'Cases with activity', (
		SELECT json_object_agg(
			to_char(months.month, 'YYYY-MM'), (
				SELECT json_agg(
			  		json_build_object(
						'date', days.day,
						'value', (
				  			SELECT n
				  			FROM metric_updates updates
				  			WHERE updates.caseoffice_id = caseoffice.id AND updates.day = days.day
						)
			  		)
				)
				FROM days
				WHERE days.day BETWEEN months.month and months.month_end
			)
		)
		FROM months
	)
  )
)
FROM case_management_caseoffice AS caseoffice;
        """
        )
        row = cursor.fetchone()
    return Response(row[0])


@api_view(['GET'])
def monthly_summary(request):
    start_month, end_month = _get_summary_months_range(request)
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
WITH
	months AS (
		SELECT date_trunc('month', months_series)::date AS month, (date_trunc('month', months_series) + interval '1 month' - interval '1 day')::date month_end
		FROM generate_series(
			'{start_month}'::timestamp,
			'{end_month}'::timestamp,
			'1 month'::interval
		) months_series
	),
	legalcase_open_close AS (
		SELECT legalcase.id, legalcase.created_at::date,
			MAX(CASE
					WHEN logchange.field = 'state' and logchange.value = 'Closed'
					THEN log.created_at
					ELSE NULL
				END)::date closed_at
		FROM case_management_legalcase legalcase
		LEFT JOIN case_management_log log ON legalcase.id = log.target_id
		LEFT JOIN case_management_logchange logchange ON log.id = logchange.log_id
		GROUP BY legalcase.id
	),
	legalcase_open_close_days AS (
		SELECT *, CASE
				WHEN closed_at IS NULL
				THEN NULL
				ELSE closed_at - created_at
			END days_created_to_closed
		FROM legalcase_open_close
	),
	legalcase_detail_by_caseoffice AS (
		SELECT legalcase.id, legalcase.created_at, legalcase.closed_at, legalcase.days_created_to_closed, case_office.caseoffice_id
		FROM legalcase_open_close_days legalcase, case_management_legalcase_case_offices case_office
		WHERE legalcase.id = case_office.legalcase_id
	),
	metric_cases_opened AS (
		SELECT legalcase.caseoffice_id, months.month, COUNT(id) n
		FROM legalcase_detail_by_caseoffice legalcase, months
		WHERE legalcase.created_at BETWEEN months.month and months.month_end
		GROUP BY legalcase.caseoffice_id, months.month
	),
	metric_cases_closed AS (
		SELECT legalcase.caseoffice_id, months.month, COUNT(id) n
		FROM legalcase_detail_by_caseoffice legalcase, months
		WHERE legalcase.closed_at BETWEEN months.month and months.month_end
		GROUP BY legalcase.caseoffice_id, months.month
	),
	metric_open_cases AS (
		SELECT legalcase.caseoffice_id, months.month, COUNT(id) n
		FROM legalcase_detail_by_caseoffice legalcase, months
		WHERE legalcase.created_at <= months.month_end AND (legalcase.closed_at IS NULL OR legalcase.closed_at >= months.month_end)
		GROUP BY legalcase.caseoffice_id, months.month
	),
	active_users_by_caseoffice AS (
		SELECT users.case_office_id, users.name, DATE_TRUNC('month', log.created_at)::date AS  month
		FROM case_management_log as log, case_management_user as users
		WHERE log.user_id = users.id
		GROUP BY users.case_office_id, users.name, month
	),
	metric_active_users AS (
		SELECT case_office_id, month, COUNT(name) as n
		FROM active_users_by_caseoffice
		GROUP BY case_office_id, month
	),
	metric_avg_open_cases_per_active_user AS (
		SELECT open_cases.caseoffice_id, open_cases.month, open_cases.n / active_users.n n
		FROM metric_open_cases open_cases, metric_active_users active_users
		WHERE open_cases.caseoffice_id = active_users.case_office_id AND open_cases.month = active_users.month
	),
	metric_avg_days_per_case AS (
		SELECT legalcase.caseoffice_id, months.month, legalcase.days_created_to_closed n
		FROM legalcase_detail_by_caseoffice legalcase, months
		WHERE legalcase.closed_at BETWEEN months.month AND months.month_end
		GROUP BY legalcase.caseoffice_id, months.month, legalcase.days_created_to_closed
	)
SELECT json_object_agg(
 	name, json_build_object(
 		'Active case officers', (
			SELECT json_agg(
				json_build_object(
					'date', to_char(months.month, 'YYYY-MM'),
					'value', (
						SELECT n
						FROM metric_active_users active_users
						WHERE active_users.case_office_id = caseoffice.id AND active_users.month = months.month
					)
				)

			 )
			FROM months
		),
		'Total cases', (
			SELECT json_agg(
				json_build_object(
					'date', to_char(months.month, 'YYYY-MM'),
					'value', (
						SELECT n
						FROM metric_open_cases open_cases
						WHERE open_cases.caseoffice_id = caseoffice.id AND open_cases.month = months.month
					)
				)

			 )
			FROM months
		),
		'Average cases per officer', (
			SELECT json_agg(
				json_build_object(
					'date', to_char(months.month, 'YYYY-MM'),
					'value', (
						SELECT n
						FROM metric_avg_open_cases_per_active_user avg_cases
						WHERE avg_cases.caseoffice_id = caseoffice.id AND avg_cases.month = months.month
					)
				)

			 )
			FROM months
		),
		'Average days per case', (
			SELECT json_agg(
				json_build_object(
					'date', to_char(months.month, 'YYYY-MM'),
					'value', (
						SELECT n + 1
						FROM metric_avg_days_per_case avg_days
						WHERE avg_days.caseoffice_id = caseoffice.id AND avg_days.month = months.month
					)
				)

			 )
			FROM months
		),
		'Cases opened', (
			SELECT json_agg(
				json_build_object(
					'date', to_char(months.month, 'YYYY-MM'),
					'value', (
						SELECT n
						FROM metric_cases_opened as opened
						WHERE opened.caseoffice_id = caseoffice.id AND opened.month = months.month
					)
				)

			 )
			FROM months
		),
		'Cases closed', (
			SELECT json_agg(
				json_build_object(
					'date', to_char(months.month, 'YYYY-MM'),
					'value', (
						SELECT n
						FROM metric_cases_closed as closed
						WHERE closed.caseoffice_id = caseoffice.id AND closed.month = months.month
					)
				)

			 )
			FROM months
		)
 	)
 )
FROM case_management_caseoffice AS caseoffice;
        """
        )
        row = cursor.fetchone()
    return Response(row[0])
