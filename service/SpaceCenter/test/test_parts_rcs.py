import unittest
import testingtools
import krpc
import time

class RCSTestBase(object):

    rcs_data = {
        'Place-Anywhere 7 Linear RCS Port': {
            'propellants': {'MonoPropellant': 1},
            'max_vac_thrust': 2000,
            'msl_isp': 100,
            'vac_isp': 240,
            'thrusters': 1
        },
        'RV-105 RCS Thruster Block': {
            'propellants': {'MonoPropellant': 1},
            'max_vac_thrust': 1000,
            'msl_isp': 100,
            'vac_isp': 240,
            'thrusters': 4
        },
        'Vernor Engine': {
            'propellants': {'LiquidFuel': 9./11., 'Oxidizer': 1},
            'max_vac_thrust': 12000,
            'msl_isp': 140,
            'vac_isp': 260,
            'thrusters': 1
        }
    }

    @classmethod
    def add_rcs_data(cls, title, data):
        for k,v in data.items():
            cls.rcs_data[title][k] = v

    def get_rcs(self, title):
        return next(iter(filter(lambda e: e.part.title == title, self.parts.rcs)))

    def set_fuel_enabled(self, value):
        for r in self.vessel.resources.all:
            r.enabled = value
        time.sleep(0.1)

class RCSTest(RCSTestBase):

    def check_properties(self, rcs):
        data = self.rcs_data[rcs.part.title]
        self.control.rcs = True
        time.sleep(0.1)
        self.assertTrue(rcs.active)
        self.assertTrue(rcs.pitch_enabled)
        self.assertTrue(rcs.yaw_enabled)
        self.assertTrue(rcs.roll_enabled)
        self.assertTrue(rcs.forward_enabled)
        self.assertTrue(rcs.up_enabled)
        self.assertTrue(rcs.right_enabled)
        self.assertClose(data['max_thrust'], rcs.max_thrust, 1)
        self.assertEqual(data['max_vac_thrust'], rcs.max_vacuum_thrust)
        self.assertEqual(data['thrusters'], len(rcs.thrusters))
        self.assertClose(data['isp'], rcs.specific_impulse, error=0.1)
        self.assertEqual(data['vac_isp'], rcs.vacuum_specific_impulse)
        self.assertEqual(data['msl_isp'], rcs.kerbin_sea_level_specific_impulse)
        self.assertEqual(sorted(data['propellants'].keys()), sorted(rcs.propellants))
        self.assertClose(data['propellants'], rcs.propellant_ratios)
        self.assertTrue(rcs.has_fuel)
        self.control.rcs = False
        time.sleep(0.1)

    def test_rcs_single(self):
        engine = self.get_rcs('Place-Anywhere 7 Linear RCS Port')
        self.check_properties(engine)

    def test_rcs_block(self):
        engine = self.get_rcs('RV-105 RCS Thruster Block')
        self.check_properties(engine)

    def test_vernor_engine(self):
        engine = self.get_rcs('Vernor Engine')
        self.check_properties(engine)

class TestPartsRCS(testingtools.TestCase, RCSTestBase):

    @classmethod
    def setUpClass(cls):
        if testingtools.connect().space_center.active_vessel.name != 'PartsRCS':
            testingtools.new_save()
            testingtools.launch_vessel_from_vab('PartsRCS')
            testingtools.remove_other_vessels()
        cls.conn = testingtools.connect(name='TestPartsRCS')
        cls.vessel = cls.conn.space_center.active_vessel
        cls.control = cls.vessel.control
        cls.parts = cls.vessel.parts

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_active_and_enabled(self):
        rcs = self.get_rcs('RV-105 RCS Thruster Block')
        self.control.rcs = True
        rcs.enabled = True
        time.sleep(0.1)
        self.assertTrue(self.control.rcs)
        self.assertTrue(rcs.enabled)
        self.assertFalse(rcs.part.shielded)
        self.assertTrue(rcs.active)
        rcs.enabled = False
        time.sleep(0.1)
        self.assertFalse(rcs.enabled)
        self.assertFalse(rcs.active)
        rcs.enabled = True
        time.sleep(0.1)
        self.assertTrue(rcs.enabled)
        self.assertTrue(rcs.active)
        self.control.rcs = False
        time.sleep(0.1)
        self.assertFalse(rcs.active)

    def test_enabled_properties(self):
        rcs = self.get_rcs('RV-105 RCS Thruster Block')
        props = (
            'enabled', 'pitch_enabled', 'yaw_enabled', 'roll_enabled',
            'forward_enabled', 'up_enabled', 'right_enabled'
        )
        for p in props:
            for x in props:
                self.assertTrue(getattr(rcs, x))
            setattr(rcs, p, False)
            time.sleep(0.1)
            for x in props:
                if x == p:
                    self.assertFalse(getattr(rcs, x))
                else:
                    self.assertTrue(getattr(rcs, x))
            setattr(rcs, p, True)
            time.sleep(0.1)
            for x in props:
                self.assertTrue(getattr(rcs, x))

    def test_has_fuel(self):
        rcs = self.get_rcs('RV-105 RCS Thruster Block')
        self.assertTrue(rcs.has_fuel)

    def test_has_no_fuel(self):
        rcs = self.get_rcs('RV-105 RCS Thruster Block')
        self.set_fuel_enabled(False)
        self.assertFalse(rcs.has_fuel)
        self.set_fuel_enabled(True)

class TestPartsRCSMSL(testingtools.TestCase, RCSTest):

    @classmethod
    def setUpClass(cls):
        testingtools.new_save()
        testingtools.launch_vessel_from_vab('PartsRCS')
        testingtools.remove_other_vessels()
        cls.conn = testingtools.connect(name='TestPartsRCSMSL')
        cls.vessel = cls.conn.space_center.active_vessel
        cls.control = cls.vessel.control
        cls.parts = cls.vessel.parts
        cls.add_rcs_data(
            'Place-Anywhere 7 Linear RCS Port',
            {'max_thrust': 842, 'isp': 101}
        )
        cls.add_rcs_data(
            'RV-105 RCS Thruster Block',
            {'max_thrust': 420, 'isp': 101}
        )
        cls.add_rcs_data(
            'Vernor Engine',
            {'max_thrust': 6503, 'isp': 140.9}
        )

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

class TestPartsRCSVacuum(testingtools.TestCase, RCSTest):

    @classmethod
    def setUpClass(cls):
        testingtools.new_save()
        testingtools.launch_vessel_from_vab('PartsRCS')
        testingtools.remove_other_vessels()
        testingtools.set_circular_orbit('Kerbin', 250000)
        cls.conn = testingtools.connect(name='TestPartsRCSVacuum')
        cls.vessel = cls.conn.space_center.active_vessel
        cls.control = cls.vessel.control
        cls.parts = cls.vessel.parts
        cls.add_rcs_data(
            'Place-Anywhere 7 Linear RCS Port',
            {'max_thrust': 2000, 'isp': 240}
        )
        cls.add_rcs_data(
            'RV-105 RCS Thruster Block',
            {'max_thrust': 1000, 'isp': 240}
        )
        cls.add_rcs_data(
            'Vernor Engine',
            {'max_thrust': 12000, 'isp': 260}
        )

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

if __name__ == '__main__':
    unittest.main()
