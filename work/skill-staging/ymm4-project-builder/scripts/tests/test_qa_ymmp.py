from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "qa_ymmp.py"
SPEC = importlib.util.spec_from_file_location("qa_ymmp", SCRIPT)
assert SPEC and SPEC.loader
qa_ymmp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa_ymmp)


def write_ymmp(path: Path, document: dict) -> None:
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(document, ensure_ascii=False).encode("utf-8"))


def base_document(file_path: str) -> dict:
    return {
        "VideoWidth": 1920,
        "VideoHeight": 1080,
        "FrameRate": 30,
        "SelectedTimelineIndex": 0,
        "Characters": [{"Name": "ずんだもん"}],
        "Timelines": [
            {
                "Length": 90,
                "MaxLayer": 2,
                "Items": [
                    {
                        "$type": "YukkuriMovieMaker.Project.Items.VoiceItem, YukkuriMovieMaker",
                        "Frame": 0,
                        "Length": 30,
                        "Layer": 2,
                        "CharacterName": "ずんだもん",
                        "Serif": "応仁の乱なのだ",
                        "Hatsuon": "おうにんのらんなのだ",
                        "VoiceLength": "00:00:00.5000000",
                        "VoiceCache": {"cache": "ok"},
                    },
                    {
                        "$type": "YukkuriMovieMaker.Project.Items.ImageItem, YukkuriMovieMaker",
                        "Frame": 30,
                        "Length": 60,
                        "Layer": 1,
                        "FilePath": file_path,
                    },
                ],
            }
        ],
    }


class QaYmmpTests(unittest.TestCase):
    def test_final_pass_path_map_expectations_baseline_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            mapped = base / "mapped"
            mapped.mkdir()
            asset = mapped / "picture.png"
            asset.write_bytes(b"png")
            project = base / "project.ymmp"
            document = base_document(r"N:\assets\picture.png")
            write_ymmp(project, document)
            original = project.read_bytes()

            baseline = base / "reference_timeline.json"
            baseline.write_text(
                json.dumps(
                    {
                        "project": {"width": 1920, "height": 1080, "fps": 30},
                        "timeline": {"length": 90},
                        "items": [
                            {
                                "index": 0,
                                "type": "Voice",
                                "frame": 0,
                                "length": 30,
                                "layer": 2,
                                "speaker": "ずんだもん",
                                "text": "応仁の乱なのだ",
                            },
                            {"index": 1, "type": "Image", "frame": 30, "length": 60, "layer": 1},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = base / "report.json"
            exit_code = qa_ymmp.main(
                [
                    str(project),
                    "--report",
                    str(report),
                    "--stage",
                    "final",
                    "--path-map",
                    rf"N:\assets={mapped}",
                    "--expect-type",
                    "VoiceItem=1",
                    "--expect-type",
                    "Image=1",
                    "--expect-file-occurrences",
                    "1",
                    "--expect-unique-files",
                    "1",
                    "--expect-max-layer",
                    "2",
                    "--reference-timeline",
                    str(baseline),
                ]
            )
            self.assertEqual(exit_code, 0)
            result = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["files"]["missing"], 0)
            self.assertEqual(result["counts"]["types"], {"Image": 1, "Voice": 1})
            self.assertEqual(project.read_bytes(), original)

    def test_structural_and_missing_file_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "broken.ymmp"
            document = base_document(str(base / "missing.png"))
            document["Timelines"][0]["Items"][0]["Frame"] = -1
            document["Timelines"][0]["Items"][0]["CharacterName"] = "unknown"
            write_ymmp(project, document)
            report = base / "report.json"
            self.assertEqual(
                qa_ymmp.main([str(project), "--report", str(report), "--stage", "final"]),
                1,
            )
            result = json.loads(report.read_text(encoding="utf-8"))
            codes = {check["code"] for check in result["checks"] if check["status"] == "FAIL"}
            self.assertTrue({"ITEM_FRAME", "UNKNOWN_CHARACTER", "FILE_MISSING"} <= codes)

    def test_stage_specific_voice_rules_and_overlap_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            asset = base / "asset.png"
            asset.write_bytes(b"png")
            project = base / "stages.ymmp"
            document = base_document(str(asset))
            voice = document["Timelines"][0]["Items"][0]
            voice["Hatsuon"] = ""
            voice["VoiceLength"] = "00:00:00"
            voice["VoiceCache"] = None
            document["Timelines"][0]["Items"][1]["Frame"] = 20
            write_ymmp(project, document)

            pre_report = base / "pre.json"
            self.assertEqual(
                qa_ymmp.main(
                    [str(project), "--report", str(pre_report), "--stage", "pre_roundtrip"]
                ),
                0,
            )
            self.assertTrue(
                any(check["code"] == "LAYER_OVERLAP" for check in json.loads(pre_report.read_text())["checks"])
                is False
            )

            post_report = base / "post.json"
            self.assertEqual(
                qa_ymmp.main(
                    [str(project), "--report", str(post_report), "--stage", "post_roundtrip"]
                ),
                1,
            )
            post_codes = {check["code"] for check in json.loads(post_report.read_text())["checks"]}
            self.assertIn("VOICE_LENGTH_EMPTY", post_codes)
            self.assertIn("VOICE_CACHE_EMPTY", post_codes)
            self.assertIn("VOICE_HATSUON_EMPTY", post_codes)

            final_report = base / "final.json"
            self.assertEqual(
                qa_ymmp.main([str(project), "--report", str(final_report), "--stage", "final"]),
                1,
            )
            final_codes = {check["code"] for check in json.loads(final_report.read_text())["checks"]}
            self.assertIn("VOICE_HATSUON_EMPTY", final_codes)

    def test_malformed_json_is_qa_failure_and_input_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "malformed.ymmp"
            project.write_bytes(b"\xef\xbb\xbf{not-json")
            original = project.read_bytes()
            report = base / "report.json"
            self.assertEqual(qa_ymmp.main([str(project), "--report", str(report)]), 1)
            result = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["checks"][0]["code"], "PARSE")
            self.assertEqual(project.read_bytes(), original)

    def test_report_cannot_replace_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project.ymmp"
            write_ymmp(project, base_document(str(Path(temporary) / "missing.png")))
            original = project.read_bytes()
            self.assertEqual(
                qa_ymmp.main([str(project), "--report", str(project)]),
                2,
            )
            self.assertEqual(project.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
