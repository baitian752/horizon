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
      .module('horizon.dashboard.project.workflow.run-task', [])
      .config(config)
      .constant('horizon.dashboard.project.workflow.run-task.modal-spec', {
        backdrop: 'static',
        size: 'lg',
        controller: 'ModalContainerController',
        template: '<wizard class="wizard" ng-controller="RunTaskWizardController"></wizard>'
      })
      .constant('horizon.dashboard.project.workflow.run-task.step-policy', {
        schedulerHints: { rules: [['compute', 'os_compute_api:os-scheduler-hints:discoverable']] },
        serverGroups: { rules: [['compute', 'os_compute_api:os-server-groups:discoverable']] }
      })
      .filter('diskFormat', diskFormat);
  
    config.$inject = [
      '$provide',
      '$windowProvider'
    ];
  
    function config($provide, $windowProvider) {
      var path = $windowProvider.$get().STATIC_URL + 'dashboard/project/workflow/run-task/';
      $provide.constant('horizon.dashboard.project.workflow.run-task.basePath', path);
    }

    function diskFormat() {
      return filter;
  
      function filter(input) {
        if (input === null || !angular.isObject(input) ||
          angular.isUndefined(input.disk_format) || input.disk_format === null) {
          return '';
        } else {
          var diskFormat = input.disk_format;
          var containerFormat = input.container_format;
          return containerFormat === 'docker' && diskFormat === 'raw' ? 'docker' : diskFormat;
        }
      }
    }
  
  })();
  