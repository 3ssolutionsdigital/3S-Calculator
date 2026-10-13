import unittest
from app.services.solar import calculate

class SolarModelTests(unittest.TestCase):
    def test_three_categories_return_plausible_positive_estimates(self):
        for category in ("residential", "commercial", "industrial"):
            with self.subTest(category=category):
                result = calculate(category, 12000, roof_area=150)
                self.assertGreater(result["annual_generation_kwh"], 0)
                self.assertGreater(result["annual_savings_inr"], 0)
                self.assertEqual(result["subsidy_inr"], 0)
                self.assertEqual(len(result["projection"]), 25)

    def test_no_roof_data_still_gives_range_and_marks_uncertainty(self):
        result = calculate("residential", 7000)
        self.assertGreater(result["capacity_kw"]["high"], result["capacity_kw"]["low"])
        self.assertEqual(result["quality"], "indicative")

    def test_rejects_zero_negative_and_excessive_bills(self):
        for amount in (0, -1, 100_000_001):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                calculate("residential", amount)

    def test_category_checks_and_industrial_never_gets_residential_subsidy(self):
        with self.assertRaises(ValueError): calculate("other", 1000)
        result = calculate("industrial", 20000)
        self.assertEqual(result["subsidy_inr"], 0)
        self.assertEqual(result["subsidy_status"], "not_applicable_to_rooftop_estimate")

if __name__ == "__main__": unittest.main()
