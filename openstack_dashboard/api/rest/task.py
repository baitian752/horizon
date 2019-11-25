from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


@urls.register
class Task(generic.View):
    
    url_regex = r'tasks/(?P<task_id>[^/]+|default)/$'

    @rest_utils.ajax()
    def get(self, request, task_id):
        
        # task = api.task
        pass


@urls.register
class Tasks(generic.View):

    url_regex = r'tasks/$'

    @rest_utils.ajax()
    def get(self, request):

        return {
            'items': [
                {
                    1: 2
                },
                {
                    3: 4
                }
            ]
        }

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        print '*' * 30
        print type(request)
        print request
        print request.DATA
        print request.user
        print request.COOKIES
        # print request.data
        print '*' * 30
        return {
            '1': 2,
            '3': 4
        }
        