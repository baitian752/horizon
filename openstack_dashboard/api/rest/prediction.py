from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


@urls.register
class Prediction(generic.View):

    url_regex = r'prediction/$'

    @rest_utils.ajax()
    def get(self, request):
        data = api.prediction.get_data(request)
        return rest_utils.JSONResponse(data)
