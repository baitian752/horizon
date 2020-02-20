from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import filters


class AuditTable(tables.DataTable):
    ACTION_DISPLAY_CHOICES = (
        ("create", pgettext_lazy("Action log of an instance", u"Create")),
        ("pause", pgettext_lazy("Action log of an instance", u"Pause")),
        ("unpause", pgettext_lazy("Action log of an instance", u"Unpause")),
        ("rebuild", pgettext_lazy("Action log of an instance", u"Rebuild")),
        ("resize", pgettext_lazy("Action log of an instance", u"Resize")),
        ("confirmresize", pgettext_lazy("Action log of an instance",
                                        u"Confirm Resize")),
        ("suspend", pgettext_lazy("Action log of an instance", u"Suspend")),
        ("resume", pgettext_lazy("Action log of an instance", u"Resume")),
        ("reboot", pgettext_lazy("Action log of an instance", u"Reboot")),
        ("stop", pgettext_lazy("Action log of an instance", u"Stop")),
        ("start", pgettext_lazy("Action log of an instance", u"Start")),
        ("shelve", pgettext_lazy("Action log of an instance", u"Shelve")),
        ("unshelve", pgettext_lazy("Action log of an instance", u"Unshelve")),
        ("migrate", pgettext_lazy("Action log of an instance", u"Migrate")),
        ("rescue", pgettext_lazy("Action log of an instance", u"Rescue")),
        ("unrescue", pgettext_lazy("Action log of an instance", u"Unrescue")),
    )

    request_id = tables.Column('request_id',
                               verbose_name=_('Request ID'))
    action = tables.Column('action', verbose_name=_('Action'),
                           display_choices=ACTION_DISPLAY_CHOICES)
    start_time = tables.Column('start_time', verbose_name=_('Start Time'),
                               filters=[filters.parse_isotime])
    user_id = tables.Column('user_id', verbose_name=_('User ID'))
    message = tables.Column('message', verbose_name=_('Message'))

    class Meta(object):
        name = 'audit'
        verbose_name = _('Instance Action List')

    def get_object_id(self, datum):
        return datum.request_id
