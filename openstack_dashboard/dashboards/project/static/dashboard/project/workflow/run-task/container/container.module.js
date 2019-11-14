/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name horizon.dashboard.project.workflow.run-task.container
   * @description
   * Dashboard module to host various container panels.
   */
  angular
    .module('horizon.dashboard.project.workflow.run-task.container', [
      'horizon.dashboard.project.workflow.run-task.container.containers',
      'horizon.dashboard.project.workflow.run-task.container.capsules',
      'horizon.dashboard.project.workflow.run-task.container.images',
      'horizon.dashboard.project.workflow.run-task.container.hosts',
      'ngRoute'
    ])
    .config(config);

  config.$inject = ['$provide', '$windowProvider'];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/project/workflow/run-task/container/';
    var root = $windowProvider.$get().WEBROOT + 'project/container/';
    $provide.constant('horizon.dashboard.project.workflow.run-task.container.basePath', path);
    $provide.constant('horizon.dashboard.project.workflow.run-task.container.webRoot', root);
  }
})();
