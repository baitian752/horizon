(function () {
    'use strict';
  
    angular
      .module('horizon.dashboard.project.workflow.run-task')
      .factory(
        'horizon.dashboard.project.workflow.run-task.modal.service',
        RunTaskModalService
      );
  
    RunTaskModalService.$inject = [
      '$uibModal',
      '$window',
      'horizon.dashboard.project.workflow.run-task.modal-spec'
    ];
  
    function RunTaskModalService($uibModal, $window, modalSpec) {
      var service = {
        open: open
      };
  
      return service;
  
      function open(launchContext) {
        var localSpec = {
          resolve: {
            launchContext: function () {
              return launchContext;
            }
          }
        };
  
        angular.extend(localSpec, modalSpec);
  
        var runTaskModal = $uibModal.open(localSpec);
        var handleModalClose = function (redirectPropertyName) {
          return function () {
            if (launchContext && launchContext[redirectPropertyName]) {
              $window.location.href = launchContext[redirectPropertyName];
            }
          };
        };
  
        return runTaskModal.result.then(
          handleModalClose('successUrl'),
          handleModalClose('dismissUrl')
        );
      }
    }
  
  })();
  