# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'tasks'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'project'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'compute'

# Python panel class of the PANEL to be added.
ADD_PANEL = 'openstack_dashboard.dashboards.project.tasks.panel.Tasks'

ADD_ANGULAR_MODULES = [
    'horizon.dashboard.project.workflow.run-task.container'
]

ADD_SCSS_FILES = [
    'dashboard/project/workflow/run-task/container/container.scss'
]

AUTO_DISCOVER_STATIC_FILES = True
