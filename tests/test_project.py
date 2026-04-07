from __future__ import annotations

import unittest
from pathlib import Path

from src.modeling import run_pipeline


class OilfieldEquipmentPredictiveMaintenanceTestCase(unittest.TestCase):
    def test_pipeline_contract(self) -> None:
        result = run_pipeline(Path(__file__).resolve().parents[1])

        self.assertEqual(result["dataset_source"], "3w_style_oilfield_telemetry_sample")
        self.assertEqual(result["asset_count"], 6)
        self.assertGreater(result["row_count"], 500)
        self.assertGreater(result["roc_auc"], 0.8)
        self.assertGreater(result["average_precision"], 0.75)


if __name__ == "__main__":
    unittest.main()
