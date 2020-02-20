(function () {
    'use strict';
  
    angular
      .module('horizon.dashboard.project.workflow.run-task')
      .controller('RunTaskModalController', RunTaskModalController);
  
    RunTaskModalController.$inject = [
      'horizon.dashboard.project.workflow.run-task.modal.service'
    ];
  
    function RunTaskModalController(modalService) {
      var ctrl = this;
  
      ctrl.openRunTaskWizard = openRunTaskWizard;
  
      function openRunTaskWizard(launchContext) {
        modalService.open(launchContext);
      }
    }
  
  })();
  