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

(function () {
  'use strict';

  angular
    .module('horizon.dashboard.project.workflow.run-task')
    .factory('RunTaskModel', RunTaskModel);

  RunTaskModel.$inject = [
    '$http',
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service',
  ]

  function RunTaskModel($http, apiService, toast) {

    var model = {

      newInstanceSpec: {},

      initialize: initialize,
      createInstance: createInstance
    };

    function initializeNewInstanceSpec() {

      model.newInstanceSpec = {

        name: null,
        virtualization: "Auto",
        cpu: 1,
        ram: 512,
        disk: 2,
        job: null,
        
        estimated_time_of_execution: -1,
        execution_frequency: -1,
        main_job: "Unspecified",
        require_hardware: "No",
        priority: 1,

        precedence_schema: null,

        auto_scaling: "No",
        
      };
    }
    
    function initialize() {
      initializeNewInstanceSpec();
      apiService.get('/api/tasks/precedence_schema/')
        .success(function(response, status, headers, config) {
          model.newInstanceSpec.precedence_schema = response.precedence_schema;
        })
        .error(function(response) {
          model.newInstanceSpec.precedence_schema = 'Execution time'
        })
    }

    function createInstance() {

      var finalSpec = angular.copy(model.newInstanceSpec);

      // $http({
      //   url: "/api/tasks/",
      //   method: "POST",
      //   data: finalSpec
      // }).success(function(response, status, headers, config) {
      //   console.log(response);
      // }).error(function(response) {
      //   console.log(response);
      // });

      return  apiService.post('/api/tasks/', finalSpec)
                .success(function(response, status, headers, config) {
                  // console.log(response);
                })
                .error(function(response) {
                  console.log(response);
                })
                .then(successMessage);

      // console.log(JSON.stringify(finalSpec));
      // alert(2333);

      // if (finalSpec.virtualization === "Virtual Machine") {
      //   return novaAPI.createServer(finalSpec).then(successMessage);
      // } else {
      //   return zunAPI.createContainer(
      //             {
      //               "name": finalSpec.meta.task_name,
      //               "image": "ubuntu",
      //               "image_driver": "docker",
      //               "command": finalSpec.user_data,
      //               "run": true,
      //               "cpu": finalSpec.vcpus,
      //               "memory": finalSpec.ram,
      //               "auto_heal": false,
      //               "mounts": [],
      //               "security_groups": [
      //                   "default"
      //               ],
      //               "interactive": true,
      //               "hints": {},
      //               // "disk": finalSpec.disk,
      //               "nets": [],
      //             }
      //          ).then(function() {
      //             var numberInstances = model.newInstanceSpec.instance_count;
      //             var message = ngettext('Scheduled creation of %s container.',
      //                                   'Scheduled creation of %s containers.',
      //                                   numberInstances);
      //             toast.add('info', interpolate(message, [numberInstances]));
      //         });
      // }
    }

    function successMessage() {
      var numberTasks = 1;
      var message = ngettext('Scheduled creation of %s task.',
                             'Scheduled creation of %s tasks.',
                             numberTasks);
      toast.add('info', interpolate(message, [numberTasks]));
    }

    function setFlavorID() {
      var vcpus = model.newInstanceSpec.vcpus;
      var ram = model.newInstanceSpec.ram;
      var disk = model.newInstanceSpec.disk;
      $.ajax({
        async: false,
        type: "GET",
        url: "/api/nova/flavors/",
        contentType: "application/json;charset=UTF-8",
        success: function (response) {
          var flavors = response.items;
          for (var i = 0; i < flavors.length; i++) {
            if (flavors[i].vcpus >= vcpus && flavors[i].ram >= ram && flavors[i].disk >= disk) {
              model.newInstanceSpec.flavor_id = flavors[i].id;
              break;
            }
          }
        },
        error: function (e) {
          console.log(e);
        }
      });
    }

    function setInstanceImage() {
      $.ajax({
        async: false,
        type: "GET",
        url: "/api/glance/images/",
        contentType: "application/json;charset=UTF-8",
        success: function (response) {
          var images = response.items;
          model.newInstanceSpec.source_id = images[0].id;
          model.newInstanceSpec.name = images[0].name;
          for (var image of images) {
            if (image.name.toLowerCase().indexOf("ubuntu") !== -1) {
              model.newInstanceSpec.source_id = image.id;
              model.newInstanceSpec.name = image.name;
              break;
            }
          }
        },
        error: function (e) {
          console.log(e);
        }
      });
    }

    function setInstanceNetwork() {
      $.ajax({
        async: false,
        type: "GET",
        url: "/api/neutron/networks/",
        contentType: "application/json;charset=UTF-8",
        success: function (response) {
          var networks = response.items;
          model.newInstanceSpec.networks.push({
            'id': networks[0].id
          });
          for (var network of networks) {
            if (network.router__external === false) {
              model.newInstanceSpec.networks[0].id = network.id;
              break;
            }
          }
        },
        error: function (e) {
          console.log(e);
        }
      });
    }

    return model;
  }

})();
