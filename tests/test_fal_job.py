"""The fal queue helper never spends money without the owner's recorded yes."""

import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

HELPER = Path(__file__).resolve().parents[1] / "skills" / "fal-ai-generation" / "scripts" / "fal_job.py"
spec = importlib.util.spec_from_file_location("fal_job", HELPER)
job = importlib.util.module_from_spec(spec)
spec.loader.exec_module(job)

APPROVAL = "https://github.com/example/game/issues/7#issuecomment-123"


def queue_sdk():
    sdk = Mock()
    sdk.Completed = type("Completed", (), {})
    sdk.InProgress = type("InProgress", (), {})
    sdk.Queued = type("Queued", (), {})
    return sdk


class FalJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fal-skill-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.input = self.base / "input.json"
        self.input.write_text('{"prompt": "a brass robot"}', encoding="utf-8")
        self.args = argparse.Namespace(endpoint="example/model", input=str(self.input), out=str(self.base / "run"),
                                       dry_run=False, env=None, owner_approval=APPROVAL)

    def test_dry_run_never_loads_sdk_or_writes_receipt(self):
        self.args.dry_run = True
        self.args.owner_approval = None
        with patch.object(job, "client", side_effect=AssertionError("SDK must not load")):
            self.assertTrue(job.submit(self.args)["dry_run"])
        self.assertFalse((self.base / "run").exists())

    def test_submission_without_owner_approval_is_refused(self):
        for value in (None, "", "yes", "https://example.com/issues/1", "http://github.com/a/b/issues/1"):
            with self.subTest(value=value):
                self.args.owner_approval = value
                sdk = Mock()
                with self.assertRaisesRegex(ValueError, "owner-approval"):
                    job.submit(self.args, sdk)
                sdk.submit.assert_not_called()
                self.assertFalse((self.base / "run" / "job.json").exists())

    def test_receipt_records_the_approval(self):
        sdk = Mock()
        sdk.submit.return_value.request_id = "demo-request"
        job.submit(self.args, sdk)
        saved = job.read_json(self.base / "run" / "job.json")
        self.assertEqual(saved["owner_approval"], APPROVAL)
        self.assertEqual(saved["status"], "submitted")

    def test_existing_receipt_blocks_duplicate_submission(self):
        sdk = Mock()
        sdk.submit.return_value.request_id = "demo-request"
        job.submit(self.args, sdk)
        with self.assertRaises(ValueError):
            job.submit(self.args, sdk)
        sdk.submit.assert_called_once()

    def test_uncertain_submission_keeps_guard(self):
        sdk = Mock()
        sdk.submit.side_effect = RuntimeError("private provider details")
        with self.assertRaisesRegex(RuntimeError, "outcome is unknown"):
            job.submit(self.args, sdk)
        saved = job.read_json(self.base / "run" / "job.json")
        self.assertEqual(saved["status"], "submission_unknown")
        self.assertNotIn("private provider details", json.dumps(saved))
        with self.assertRaises(ValueError):
            job.submit(self.args, sdk)
        sdk.submit.assert_called_once()

    def test_placeholder_is_not_submitted(self):
        self.input.write_text('{"image_urls": ["https://example.invalid/input.png"]}', encoding="utf-8")
        sdk = Mock()
        with self.assertRaises(ValueError):
            job.submit(self.args, sdk)
        sdk.submit.assert_not_called()

    def test_upload_needs_approval(self):
        source = self.base / "ref.png"
        source.write_bytes(b"png")
        sdk = Mock()
        args = argparse.Namespace(file=str(source), out=str(self.base / "upload.json"), env=None, owner_approval=None)
        with self.assertRaisesRegex(ValueError, "owner-approval"):
            job.upload(args, sdk)
        sdk.upload_file.assert_not_called()
        args.owner_approval = APPROVAL
        sdk.upload_file.return_value = "https://fal.media/files/ref.png"
        job.upload(args, sdk)
        self.assertEqual(job.read_json(self.base / "upload.json")["owner_approval"], APPROVAL)

    def test_processing_result_never_fetches_or_resubmits(self):
        sdk = queue_sdk()
        sdk.status.return_value = sdk.InProgress()
        receipt = self.base / "job.json"
        job.save_json(receipt, {"endpoint_id": "example/model", "request_id": "demo"})
        self.assertEqual(job.resume(argparse.Namespace(command="result", job=str(receipt), env=None), sdk)["status"],
                         "IN_PROGRESS")
        sdk.result.assert_not_called()
        sdk.submit.assert_not_called()

    def test_completed_provider_error_is_not_downloaded(self):
        sdk = queue_sdk()
        sdk.status.return_value = sdk.Completed()
        sdk.result.return_value = {"error": "model failed"}
        receipt = self.base / "job.json"
        job.save_json(receipt, {"endpoint_id": "example/model", "request_id": "demo"})
        with patch.object(job, "download_result") as download:
            with self.assertRaisesRegex(RuntimeError, "Provider returned an error"):
                job.resume(argparse.Namespace(command="result", job=str(receipt), env=None), sdk)
            download.assert_not_called()

    def test_nested_models_and_material_maps_are_discovered(self):
        result = {"images": [{"url": "https://example.invalid/normal.png", "map_type": "normal"}],
                  "model_urls": {"glb": "https://example.invalid/model.glb"}, "text": "ordinary prose"}
        self.assertEqual([v["url"] for v in job.media_urls(result)],
                         ["https://example.invalid/normal.png", "https://example.invalid/model.glb"])

    def test_saved_result_does_not_require_provider_history(self):
        receipt = self.base / "job.json"
        job.save_json(receipt, {"endpoint_id": "example/model", "request_id": "demo"})
        job.save_json(self.base / "result.json", {"description": "Completed text result"})
        with patch.object(job, "client", side_effect=AssertionError("No provider request should be needed")):
            result = job.resume(argparse.Namespace(command="result", job=str(receipt), env=None))
        self.assertEqual(result["status"], "result_saved")
        self.assertEqual(result["review"], "pending")


if __name__ == "__main__":
    unittest.main()
