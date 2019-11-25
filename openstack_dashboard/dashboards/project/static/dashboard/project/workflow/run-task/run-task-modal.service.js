/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
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
  