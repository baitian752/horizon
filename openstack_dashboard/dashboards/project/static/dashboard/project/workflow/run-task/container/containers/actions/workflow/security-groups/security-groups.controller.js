/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  angular
    .module('horizon.dashboard.project.workflow.run-task.container.containers')
    .controller('horizon.dashboard.project.workflow.run-task.container.containers.workflow.security-group',
      SecurityGroupsController);

  SecurityGroupsController.$inject = [
    '$scope',
    'horizon.dashboard.project.workflow.run-task.container.basePath'
  ];

  /**
   * @ngdoc controller
   * @name SecurityGroupsController
   * @param {Object} containerModel
   * @param {string} basePath
   * @description
   * Allows selection of security groups.
   * @returns {undefined} No return value
   */
  function SecurityGroupsController($scope, basePath) {
    var ctrl = this;

    ctrl.tableData = {
      available: $scope.model.availableSecurityGroups,
      allocated: $scope.model.security_groups,
      displayedAvailable: [],
      displayedAllocated: []
    };

    /* eslint-disable max-len */
    ctrl.tableDetails = basePath + 'containers/actions/workflow/security-groups/security-group-details.html';
    /* eslint-enable max-len */

    ctrl.tableHelp = {
      /* eslint-disable max-len */
      noneAllocText: gettext('Select one or more security groups from the available groups below.'),
      /* eslint-enable max-len */
      availHelpText: gettext('Select one or more')
    };

    ctrl.tableLimits = {
      maxAllocation: -1
    };

    ctrl.filterFacets = [
      {
        label: gettext('Name'),
        name: 'name',
        singleton: true
      },
      {
        label: gettext('Description'),
        name: 'description',
        singleton: true
      }
    ];
  }
})();
