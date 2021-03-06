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
    data['job'] = data['job'].strip() if data['job'] else 'echo Hello OpenStack'
    if data['estimated_time_of_execution'] < 0:
        data['estimated_time_of_execution'] = sys.maxint
    if data['execution_frequency'] < 0:
        data['execution_frequency'] = sys.maxint
    data['main_job'] = data['main_job'].strip() if data['main_job'] else 'Unspecified'
    # data['created_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['created_timestamp'] = time.time()

    return data


@urls.register
class Tasks(generic.View):

    url_regex = r'tasks/$'

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        data = format_data(request.DATA)
        tasks = api.task.Tasks('tasks')
        tasks.update_precedence_schema(data['precedence_schema'])
        data.pop('precedence_schema')
        tasks.add(data)


@urls.register
class Priority(generic.View):

    url_regex = r'tasks/precedence_schema/$'

    @rest_utils.ajax()
    def get(self, request):
        return {
            'precedence_schema': \
                api.task.Tasks('tasks').get_precedence_schema()
        }
