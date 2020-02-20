from django.utils.translation import ugettext_lazy as _

import horizon


class Tasks(horizon.Panel):
    name = _("Tasks")
    slug = 'tasks'
    permissions = ('openstack.services.compute',)
