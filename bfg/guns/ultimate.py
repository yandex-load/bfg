'''
Ultimate gun
'''
import imp
from .base import GunBase, Sample
from queue import Full
import time
from contextlib import contextmanager
import logging


logger = logging.getLogger(__name__)


class UltimateGun(GunBase):
    '''
    Scenario gun imports SCENARIOS from a user-provided python module. Then
    it uses task.scenario field to decide which scenario to activate

    User should use self.measure context to collect samples
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        module_name = self.get_option("module_name", "gun")
        module_path = self.get_option("module_path", ".")
        class_name = self.get_option("class_name", "LoadTest")
        self.init_param = self.get_option("init_param", "")
        if module_path:
            module_path = module_path.split()
        else:
            module_path = None
        fp, pathname, description = imp.find_module(module_name, module_path)
        try:
            self.module = imp.load_module(
                module_name, fp, pathname, description)
        finally:
            if fp:
                fp.close()
        test_class = getattr(self.module, class_name, None)
        if not isinstance(test_class, type):
            raise NotImplementedError(
                "Class definition for '%s' was not found in '%s' module" %
                (class_name, module_name))
        self.load_test = test_class(self)

    def setup(self):
        if callable(getattr(self.load_test, "setup", None)):
            self.load_test.setup(self.init_param)

    def teardown(self):
        if callable(getattr(self.load_test, "teardown", None)):
            self.load_test.teardown()

    def shoot(self, task):
        marker = task.marker.rsplit("#", 1)[0]  # support enum_ammo
        if not marker:
            marker = "default"
        scenario = getattr(self.load_test, marker, None)
        if callable(scenario):
            try:
                scenario(task)
            except Exception as e:
                logger.warning(
                    "Scenario %s failed with %s",
                    marker, e, exc_info=True)
        else:
            logger.warning("Scenario not found: %s", marker)
