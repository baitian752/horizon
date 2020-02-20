(function () {
    'use strict';
  
    angular
      .module('horizon.dashboard.project.workflow.run-task')
      .factory('horizon.dashboard.project.workflow.run-task.workflow', RunTaskWorkflow);
  
    RunTaskWorkflow.$inject = [
      'horizon.dashboard.project.workflow.run-task.basePath',
      'horizon.dashboard.project.workflow.run-task.step-policy',
      'horizon.app.core.workflow.factory'
    ];
  
    function RunTaskWorkflow(basePath, stepPolicy, dashboardWorkflow) {
      return dashboardWorkflow({
        title: gettext('Run Task'),
  
        steps: [
          {
            id: 'configuration',
            title: gettext('Configuration'),
            templateUrl: basePath + 'configuration/configuration.html',
            helpUrl: basePath + 'configuration/configuration.help.html',
            formName: 'RunTaskConfigurationForm'
          }
        ],
  
        btnText: {
          finish: gettext('Run Task')
        },
  
        btnIcon: {
          finish: 'fa-cloud-upload'
        }
      });
    }
  
  })();
  