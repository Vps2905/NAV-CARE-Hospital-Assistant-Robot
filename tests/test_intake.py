import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from patient_demo import reason_to_destination

class RoutingTests(unittest.TestCase):
    def test_knee(self):
        self.assertEqual(reason_to_destination('knee pain').destination, 'orthopedics')
    def test_fever(self):
        self.assertEqual(reason_to_destination('fever and cough').destination, 'general_medicine')
    def test_lab_referral_needed(self):
        self.assertEqual(reason_to_destination('blood test').destination, 'nurse_station')
        self.assertEqual(reason_to_destination('blood test', True).destination, 'laboratory')
    def test_urgent_stops(self):
        d = reason_to_destination('chest pain and dizziness')
        self.assertTrue(d.urgent)
        self.assertIsNone(d.destination)
    def test_unknown_escalates(self):
        self.assertEqual(reason_to_destination('unusual sensation').destination, 'nurse_station')

if __name__ == '__main__':
    unittest.main()
