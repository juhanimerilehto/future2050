import json, os, sys, unittest
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import core, scenarios as SC, uncertainty as UQ
from params import central, HOURS0, P


class UnitModel(unittest.TestCase):
    def test_reproduces_hre2_unit_table(self):
        """2025 machine reproduces hre-2.0.0 Appendix B within 0.3 %."""
        pub = {"factory": 1719, "warehouse": 1941, "household": 1273}
        for pr, v in pub.items():
            pc = central()
            e, *_ = core.unit_energy(pc, core.active_power(pc, pr, 2025), HOURS0[pr], pr)
            self.assertLess(abs(e[0] / v - 1), 0.003, pr)

    def test_charger_cap(self):
        pc = central()
        Pa = np.array([2.0]); e, Hw, Hch, *_ , cap = core.unit_energy(pc, Pa, np.array([8000.0]), "factory")
        self.assertTrue(cap[0]); self.assertLessEqual(Hw[0] + Hch[0], 8760.0 + 1e-6)


class Legacy(unittest.TestCase):
    def test_reproduces_hre2_reference(self):
        leg = core.legacy_2035()
        self.assertLess(abs(leg["stock"] / 9.93e6 - 1), 0.005)
        self.assertLess(abs(leg["ry"] / 7.93e6 - 1), 0.005)
        self.assertLess(abs(leg["twh"] / 13.3 - 1), 0.005)


class Fleet(unittest.TestCase):
    def test_exposure_bounded_by_stock(self):
        o = core.run(central())
        S = o["stock"][0]; RY = o["ry"][0]
        # exposure during year t cannot exceed max(opening, closing) stock
        opening = np.concatenate([[0], S[:-1]])
        self.assertTrue(np.all(RY <= np.maximum(opening, S) * 1.0001 + o["q"][0]))

    def test_anchor_2026(self):
        o = core.run(central())
        self.assertAlmostEqual(o["q"][0, 1] / central()["q26"], 1.0, places=6)

    def test_monotone_in_ceiling(self):
        lo, hi = central(), central()
        lo["Qmax"], hi["Qmax"] = 5e7, 2e8
        self.assertLess(core.run(lo)["twh"][0, -1], core.run(hi)["twh"][0, -1])

    def test_exactly_identified_scenarios_hit_anchors(self):
        for n in ("constrained", "abundance"):
            Q, k, res = SC.fit(n)
            for v in res.values():
                self.assertLess(abs(v), 0.01, n)


class Peaks(unittest.TestCase):
    def test_charging_profile_reconciles_with_energy(self):
        """Mean of the hourly world charging profile equals stock x intensity / 8760 (no extra factor)."""
        stock, kwh = 7.0e8, 1900.0
        pk = core.charging_peaks(stock, kwh)
        for case in ("unmanaged", "managed"):
            self.assertAlmostEqual(pk[case]["world_profile"].mean(), stock * kwh / 8760 / 1e6, places=6)


class Sobol(unittest.TestCase):
    def test_ishigami(self):
        S1, ST = UQ.ishigami_check()
        np.testing.assert_allclose(S1, [0.314, 0.442, 0.0], atol=0.03)
        np.testing.assert_allclose(ST, [0.558, 0.442, 0.244], atol=0.03)


class Outputs(unittest.TestCase):
    def test_manuscript_numbers_come_from_results(self):
        out = os.path.join(os.path.dirname(HERE), "outputs")
        res = json.load(open(os.path.join(out, "results.json")))
        nums = open(os.path.join(out, "numbers.tex")).read()
        ref = res["scenarios"]["reference"]["twh2050"]
        self.assertIn(f"{ref:,.0f}".replace(",", "\\,"), nums)


if __name__ == "__main__":
    unittest.main()
