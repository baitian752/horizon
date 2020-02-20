(function () {
  'use strict';

  var MAX_SCRIPT_SIZE = 16 * 1024;

  angular
    .module('horizon.dashboard.project.workflow.run-task')
    .controller('RunTaskConfigurationController', RunTaskConfigurationController);

  function RunTaskConfigurationController() {
    var ctrl = this;
    ctrl.title = gettext("Customization Script");
    ctrl.MAX_SCRIPT_SIZE = MAX_SCRIPT_SIZE;

    ctrl.diskConfigOptions = [
      { value: 'AUTO', text: gettext('Automatic') },
      { value: 'MANUAL', text: gettext('Manual') }
    ];
  }
})();
