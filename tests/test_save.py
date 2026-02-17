from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pvz.save import SaveModelV1, SaveStore


class SaveTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "save.json"
            store = SaveStore(path)
            model = SaveModelV1()
            model.shop["coins"] = 123
            store.save(model)
            loaded = store.load()
            self.assertEqual(loaded.shop["coins"], 123)


if __name__ == "__main__":
    unittest.main()
