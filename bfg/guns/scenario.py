'''
Scenario gun
'''
import sys
import logging


LOG = logging.getLogger(__name__)


class ScenarioGun(object):
    '''
    Scenario gun imports SCENARIOS from a user-provided python module. Then
    it uses task.scenario field to decide which scenario to activate

    User should use @measure context from measure.py module to collect samples
    '''

    def __init__(self, module_name, module_path=""):
        if module_path:
            sys.path.append(module_path)
        self.module = __import__(module_name)
        self.scenarios = self.module.SCENARIOS

    def shoot(self, task, results):
        scenario = self.scenarios.get(task.scenario, None)
        if scenario:
            try:
                scenario(task, results)
            except RuntimeError as e:
                LOG.warning("Scenario %s failed with %s", task.scenario, e)
        else:
            LOG.warning("Scenario not found: %s", task.scenario)
