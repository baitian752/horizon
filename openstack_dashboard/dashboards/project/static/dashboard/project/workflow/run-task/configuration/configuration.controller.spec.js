(function() {
  'use strict';

  describe('Run Task Configuration Step', function() {

    describe('RunTaskConfigurationController', function() {
      var ctrl;

      beforeEach(module('horizon.dashboard.project.workflow.run-task'));

      beforeEach(inject(function($controller) {
        ctrl = $controller('RunTaskConfigurationController');
      }));

      it('has correct disk configuration options', function() {
        expect(ctrl.diskConfigOptions).toBeDefined();
        expect(ctrl.diskConfigOptions.length).toBe(2);
        var vals = ctrl.diskConfigOptions.map(function(x) {
          return x.value;
        });
        expect(vals).toContain('AUTO');
        expect(vals).toContain('MANUAL');
      });

      it('sets the user data max script size', function() {
        expect(ctrl.MAX_SCRIPT_SIZE).toBe(16 * 1024);
      });

    });

  });

})();
