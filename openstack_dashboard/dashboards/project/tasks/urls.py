from django.conf.urls import url

from openstack_dashboard.dashboards.project.tasks import views


INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'
INSTANCES_KEYPAIR = r'^(?P<instance_id>[^/]+)/(?P<keypair_name>[^/]+)/%s$'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^launch$', views.LaunchInstanceView.as_view(), name='launch'),
    url(r'^(?P<instance_id>[^/]+)/$',
        views.DetailView.as_view(), name='detail'),
    url(INSTANCES % 'update', views.UpdateView.as_view(), name='update'),
    url(INSTANCES % 'rebuild', views.RebuildView.as_view(), name='rebuild'),
    url(INSTANCES % 'serial', views.SerialConsoleView.as_view(),
        name='serial'),
    url(INSTANCES % 'console', views.console, name='console'),
    url(INSTANCES % 'auto_console', views.auto_console, name='auto_console'),
    url(INSTANCES % 'vnc', views.vnc, name='vnc'),
    url(INSTANCES % 'spice', views.spice, name='spice'),
    url(INSTANCES % 'rdp', views.rdp, name='rdp'),
    url(INSTANCES % 'resize', views.ResizeView.as_view(), name='resize'),
    url(INSTANCES_KEYPAIR % 'decryptpassword',
        views.DecryptPasswordView.as_view(), name='decryptpassword'),
    url(INSTANCES % 'disassociate',
        views.DisassociateView.as_view(), name='disassociate'),
    url(INSTANCES % 'attach_interface',
        views.AttachInterfaceView.as_view(), name='attach_interface'),
    url(INSTANCES % 'detach_interface',
        views.DetachInterfaceView.as_view(), name='detach_interface'),
    url(r'^(?P<instance_id>[^/]+)/attach_volume/$',
        views.AttachVolumeView.as_view(),
        name='attach_volume'
        ),
    url(r'^(?P<instance_id>[^/]+)/detach_volume/$',
        views.DetachVolumeView.as_view(),
        name='detach_volume'
        ),
    url(r'^(?P<instance_id>[^/]+)/ports/(?P<port_id>[^/]+)/update$',
        views.UpdatePortView.as_view(), name='update_port'),
    url(INSTANCES % 'rescue', views.RescueView.as_view(), name='rescue'),
]
