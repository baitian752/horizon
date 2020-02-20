(function () {
    'use strict';
  
    angular
      .module('horizon.dashboard.project.workflow.run-task')
      .controller('RunTaskWizardController', RunTaskWizardController);
  
    RunTaskWizardController.$inject = [
      '$scope',
      'RunTaskModel',
      'horizon.dashboard.project.workflow.run-task.workflow'
    ];
  
    function RunTaskWizardController($scope, RunTaskModel, RunTaskWorkflow) {
      // Note: we set these attributes on the $scope so that the scope inheritance used all
      // through the run task wizard continues to work.
      $scope.workflow = RunTaskWorkflow;     // eslint-disable-line angular/controller-as
      $scope.model = RunTaskModel;           // eslint-disable-line angular/controller-as
      $scope.model.initialize();
      $scope.submit = $scope.model.createInstance;  // eslint-disable-line angular/controller-as
    }
  
  })();
  