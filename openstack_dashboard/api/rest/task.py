import sys
import time
from math import ceil

from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


api.task.Schedule().start()


def format_data(data):
    data['name'] = data['name'].strip() if data['name'] else 'name'
    data['status'] = 'ready'
    data['cpu'] = int(ceil(data['cpu']))
    data['ram'] = int(ceil(data['ram']))
    data['disk'] = int(ceil(data['disk']))
    data['job'] = data['job'].strip() if data['job'] else 'echo hello'
    if data['estimated_time_of_execution'] < 0:
        data['estimated_time_of_execution'] = sys.maxint
    if data['execution_frequency'] < 0:
        data['execution_frequency'] = sys.maxint
    data['main_job'] = data['main_job'].strip() if data['main_job'] else 'Unspecified'
    # data['created_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['created_timestamp'] = time.time()

    return data


# @urls.register
# class Task(generic.View):

#     url_regex = r'tasks/(?P<task_id>[^/]+|default)/$'

#     @rest_utils.ajax()
#     def get(self, request, task_id):

#         # task = api.task
#         pass


@urls.register
class Tasks(generic.View):

    url_regex = r'tasks/$'

    # @rest_utils.ajax()
    # def get(self, request):

    #     return {
    #         'items': [
    #             {
    #                 1: 2
    #             },
    #             {
    #                 3: 4
    #             }
    #         ]
    #     }

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        # print '*' * 30
        # print 'type(request): %s' % type(request)
        # print 'request: %s' % request
        # print 'type(request.DATA): %s' % type(request.DATA)
        # print 'request.DATA: %s' % request.DATA
        # print 'request.user: %s' % request.user
        # print 'request.COOKIES: %s' % request.COOKIES
        # print '*' * 30
        data = format_data(request.DATA)
        api.task.Tasks(api.task.table_name).update_precedence_schema(
            data['precedence_schema'])
        data.pop('precedence_schema')
        api.task.Tasks(api.task.table_name).add(data)
        # return {
        #     '1': 2,
        #     '3': 4
        # }


@urls.register
class Priority(generic.View):

    url_regex = r'tasks/precedence_schema/$'

    @rest_utils.ajax()
    def get(self, request):
        return {
            'precedence_schema': \
                api.task.Tasks(api.task.table_name).get_precedence_schema()
        }
