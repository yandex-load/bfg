class CustomGun(AbstractPlugin):
    SECTION = 'custom_gun'

    def __init__(self, core):
        self.log = logging.getLogger(__name__)
        AbstractPlugin.__init__(self, core)
        module_path = self.get_option("module_path", "")
        module_name = self.get_option("module_name")
        if module_path:
            sys.path.append(module_path)
        self.module = __import__(module_name)

    def shoot(self, missile, marker, results):
        self.module.shoot(missile, marker, results)

class ScenarioGun(AbstractPlugin):
    SECTION = 'scenario_gun'

    def __init__(self, core):
        self.log = logging.getLogger(__name__)
        AbstractPlugin.__init__(self, core)
        module_path = self.get_option("module_path", "")
        module_name = self.get_option("module_name")
        if module_path:
            sys.path.append(module_path)
        self.module = __import__(module_name)
        self.scenarios = self.module.SCENARIOS

    def shoot(self, missile, marker, results):
        scenario = self.scenarios.get(marker, None)
        if scenario:
            try:
                scenario(missile, marker, results)
            except RuntimeError as e:
                self.log.warning("Scenario %s failed with %s", marker, e)
        else:
            self.log.warning("Scenario not found: %s", marker)
