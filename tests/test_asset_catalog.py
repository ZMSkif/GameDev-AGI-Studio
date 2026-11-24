import copy
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import asset_catalog  # noqa: E402


class AssetCatalogTest(unittest.TestCase):
    def setUp(self):
        self.catalog, self.packs = asset_catalog.load()

    def run_cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = asset_catalog.main(list(args))
        return code, out.getvalue()

    def test_shipped_files_are_valid_and_table_is_current(self):
        code, out = self.run_cli("check")
        self.assertEqual(code, 0, out)
        self.assertGreater(len(self.catalog["sources"]), 80)
        self.assertGreater(len(self.packs["packs"]), 600)

    def test_unknown_values_and_missing_licence_are_reported(self):
        bad = copy.deepcopy(self.catalog)
        bad["sources"][0]["commercial"] = "maybe"
        packs = copy.deepcopy(self.packs)
        packs["packs"][0]["licence"] = ""
        found = asset_catalog.problems(bad, packs)
        self.assertTrue(any("commercial" in f for f in found))
        self.assertTrue(any("licence" in f for f in found))

    def test_duplicate_id_is_reported(self):
        bad = copy.deepcopy(self.catalog)
        bad["sources"].append(copy.deepcopy(bad["sources"][0]))
        self.assertTrue(any("duplicate" in f for f in asset_catalog.problems(bad, self.packs)))

    def test_filters(self):
        _, out = self.run_cli("list", "--kind", "fonts", "--json")
        rows = json.loads(out)
        self.assertTrue(rows)
        self.assertTrue(all("fonts" in r["kinds"] for r in rows))
        _, out = self.run_cli("packs", "--kind", "materials", "--find", "leather", "--json")
        rows = json.loads(out)
        self.assertTrue(rows)
        self.assertTrue(all(r["kind"] == "materials" for r in rows))

    def test_avoided_characters_are_not_offered_as_packs(self):
        names = {p["name"] for p in self.packs["packs"]}
        self.assertFalse(names & set(self.catalog["avoid"]["third_party_characters"]))


if __name__ == "__main__":
    unittest.main()
