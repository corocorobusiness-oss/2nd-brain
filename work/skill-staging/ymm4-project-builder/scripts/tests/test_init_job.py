from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "init_job.py"
SPEC = importlib.util.spec_from_file_location("init_job", SCRIPT)
assert SPEC and SPEC.loader
init_job = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(init_job)


class InitJobTests(unittest.TestCase):
    def test_scaffold_hashes_and_resume_are_non_destructive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            sources = base / "sources"
            sources.mkdir()
            script = sources / "original.csv"
            dictionary = sources / "original.dic"
            reference = sources / "original.mp4"
            template = sources / "original.ymmp"
            script.write_bytes("ずんだもん,応仁の乱\n".encode("utf-8"))
            dictionary.write_bytes(b"dictionary")
            reference.write_bytes(b"mp4")
            template.write_bytes(b"\xef\xbb\xbf{}")

            root = base / "jobs"
            arguments = [
                "--job-id",
                "JOB-2026-001",
                "--name",
                "応仁の乱",
                "--root",
                str(root),
                "--script",
                str(script),
                "--dictionary",
                str(dictionary),
                "--reference",
                str(reference),
                "--master-template",
                str(template),
                "--mode",
                "replicate",
                "--ymm4-version",
                "4.53.0.9",
            ]
            self.assertEqual(init_job.main(arguments), 0)

            job = root / "JOB-2026-001"
            for relative in init_job.DIRECTORIES:
                self.assertTrue((job / relative).is_dir(), relative)
            self.assertEqual((job / "input/script.csv").read_bytes(), script.read_bytes())
            self.assertEqual(
                (job / "input/pronunciation.dic").read_bytes(), dictionary.read_bytes()
            )
            self.assertEqual((job / "input/reference.mp4").read_bytes(), b"mp4")
            self.assertEqual((job / "template/master_template.ymmp").read_bytes(), template.read_bytes())

            state_path = job / "reports/job_state.json"
            lock_path = job / "reports/project.lock.json"
            state_before = state_path.read_bytes()
            lock_before = lock_path.read_bytes()
            state = json.loads(state_before)
            lock = json.loads(lock_before)
            self.assertEqual(state["status"], "NEW")
            self.assertEqual(lock["project"], {"fps": 30.0, "height": 1080, "width": 1920})
            self.assertEqual(
                lock["inputs"]["script"]["sha256"],
                hashlib.sha256(script.read_bytes()).hexdigest().upper(),
            )

            self.assertEqual(init_job.main(arguments), 2)
            self.assertEqual(init_job.main(arguments + ["--resume"]), 0)
            self.assertEqual(state_path.read_bytes(), state_before)
            self.assertEqual(lock_path.read_bytes(), lock_before)

    def test_resume_rejects_different_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            first = base / "first.csv"
            second = base / "second.csv"
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")
            common = ["--job-id", "JOB-1", "--name", "test", "--root", str(base / "jobs")]
            self.assertEqual(init_job.main(common + ["--script", str(first)]), 0)
            self.assertEqual(
                init_job.main(common + ["--script", str(second), "--resume"]), 2
            )
            self.assertEqual((base / "jobs/JOB-1/input/script.csv").read_text(), "first")

    def test_path_traversal_and_invalid_dimensions_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(
                init_job.main(
                    [
                        "--job-id",
                        "../escape",
                        "--name",
                        "test",
                        "--root",
                        temporary,
                    ]
                ),
                2,
            )
            self.assertEqual(
                init_job.main(
                    [
                        "--job-id",
                        "JOB-2",
                        "--name",
                        "test",
                        "--root",
                        temporary,
                        "--width",
                        "0",
                    ]
                ),
                2,
            )


if __name__ == "__main__":
    unittest.main()
