#!/usr/bin/env python3

import importlib.machinery
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / ".local/bin/krisp-import"
loader = importlib.machinery.SourceFileLoader("krisp_import", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
krisp = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = krisp
loader.exec_module(krisp)


def attendee(name, attendee_type="required", response="accepted"):
    return {
        "display_name": name,
        "email": "",
        "type": attendee_type,
        "response": response,
    }


def event(*names, title="Test Meeting", start="2026-07-30T10:00:00-05:00"):
    return {
        "event_id": "event-1",
        "title": title,
        "start": start,
        "end": "2026-07-30T10:30:00-05:00",
        "organizer": {"display_name": "Jason More", "email": "jasonmore"},
        "attendees": [attendee(name) for name in names],
    }


class AttributionTests(unittest.TestCase):
    def test_exact_user_corrected_set_match(self):
        result = krisp.attribution(event("David Poll"), ["Jason More", "David Poll"])
        self.assertTrue(result["exact_speaker_set_match"])
        self.assertEqual([], result["attribution_rejection_reasons"])

    def test_wrong_one_on_one_name(self):
        result = krisp.attribution(event("David Poll"), ["Jason More", "Blake Williams"])
        self.assertFalse(result["exact_speaker_set_match"])
        self.assertIn("missing Krisp speakers: David Poll", result["attribution_rejection_reasons"])

    def test_extra_krisp_name_rejects_all(self):
        result = krisp.attribution(
            event("David Poll"), ["Jason More", "David Poll", "Blake Williams"]
        )
        self.assertFalse(result["exact_speaker_set_match"])
        self.assertIn("extra Krisp speakers: Blake Williams", result["attribution_rejection_reasons"])

    def test_missing_workiq_participant(self):
        result = krisp.attribution(event("David Poll"), ["Jason More"])
        self.assertFalse(result["exact_speaker_set_match"])
        self.assertIn("missing Krisp speakers: David Poll", result["attribution_rejection_reasons"])

    def test_generic_speaker_label(self):
        result = krisp.attribution(event("David Poll"), ["Jason More", "Speaker 1"])
        self.assertFalse(result["exact_speaker_set_match"])
        self.assertIn("generic Krisp label: Speaker 1", result["attribution_rejection_reasons"])

    def test_group_non_invitee(self):
        result = krisp.attribution(
            event("David Poll", "Jon Fuchs"),
            ["Jason More", "David Poll", "Jon Fuchs", "Maya Ross"],
        )
        self.assertFalse(result["exact_speaker_set_match"])
        self.assertIn("extra Krisp speakers: Maya Ross", result["attribution_rejection_reasons"])

    def test_declined_attendee_excluded(self):
        value = event("David Poll")
        value["attendees"].append(attendee("Blake Williams", response="declined"))
        result = krisp.attribution(value, ["Jason More", "David Poll"])
        self.assertTrue(result["exact_speaker_set_match"])

    def test_resource_room_excluded(self):
        value = event("David Poll")
        value["attendees"].append(attendee("Conference Room 1", attendee_type="room"))
        result = krisp.attribution(value, ["Jason More", "David Poll"])
        self.assertTrue(result["exact_speaker_set_match"])

    def test_known_email_alias_normalized(self):
        value = event("David Poll")
        value["attendees"][0]["display_name"] = ""
        value["attendees"][0]["email"] = "davidpoll@example.com"
        result = krisp.attribution(value, ["Jason More", "David Poll"])
        self.assertTrue(result["exact_speaker_set_match"])


class RoutingTests(unittest.TestCase):
    def test_overlapping_calendar_meetings_are_ambiguous(self):
        fixture = json.loads(
            (Path(__file__).parent / "fixtures/calendar.json").read_text(encoding="utf-8")
        )
        meeting = {
            "name": "Platform Sync",
            "date": "2026-07-30T14:00:00-05:00",
        }
        matched, reason = krisp.match_event(meeting, fixture["events"])
        self.assertIsNone(matched)
        self.assertEqual("ambiguous overlapping calendar events", reason)

    def test_no_attendee_list_routes_unresolved_group(self):
        route, invitees, reason = krisp.route_for_event(event())
        self.assertEqual(krisp.GROUP_ROOT, route)
        self.assertEqual([], invitees)
        self.assertEqual("no usable non-Jason calendar invitees", reason)

    def test_existing_wrong_path_detected(self):
        vault = Path(__file__).parent / "fixtures/vault"
        wrong = vault / "one-one/jfuchs/2026-07-30 10.00.00 Jason _ David 1_1.md"
        meeting = {
            "meeting_id": "abc123",
            "name": "Jason / David 1:1",
            "date": "2026-07-30T10:00:00-05:00",
        }
        found = krisp.existing_import(vault, meeting, {"meetings": {}})
        self.assertEqual(wrong, found)
        self.assertEqual("raw transcript\n", wrong.read_text(encoding="utf-8"))

    def test_utc_near_midnight_uses_manifest_local_date(self):
        timezone = ZoneInfo("America/Chicago")
        meeting = {
            "meeting_id": "midnight",
            "name": "Late Platform Sync",
            "date": "2026-07-31T04:30:00Z",
        }
        self.assertTrue(krisp.meeting_on_target_date(meeting, "2026-07-30", timezone))
        self.assertTrue(krisp.safe_filename(meeting, timezone).startswith("2026-07-30 23.30.00"))


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(
            (Path(__file__).parent / "fixtures/calendar.json").read_text(encoding="utf-8")
        )

    def test_list_top_level_is_invalid(self):
        self.assertFalse(krisp.valid_manifest([]))
        events, reason, timezone = krisp.manifest_routing([])
        self.assertEqual([], events)
        self.assertEqual("invalid calendar manifest schema", reason)
        self.assertEqual("America/Chicago", timezone.key)

    def test_bad_timestamp_is_invalid(self):
        self.manifest["events"][0]["start"] = "not-a-timestamp"
        self.assertFalse(krisp.valid_manifest(self.manifest))
        events, reason, _ = krisp.manifest_routing(self.manifest)
        self.assertEqual([], events)
        self.assertEqual("invalid calendar manifest schema", reason)

    def test_bad_timezone_is_invalid(self):
        self.manifest["timezone"] = "Mars/Olympus"
        self.assertFalse(krisp.valid_manifest(self.manifest))
        events, reason, _ = krisp.manifest_routing(self.manifest)
        self.assertEqual([], events)
        self.assertEqual("invalid calendar manifest schema", reason)

    def test_malformed_json_degrades_to_unresolved_routing(self):
        path = Path(__file__).parent / "fixtures/malformed-manifest.json"
        events, reason, timezone = krisp.load_manifest_routing(path)
        self.assertEqual([], events)
        self.assertEqual(
            "invalid calendar manifest schema: unable to parse JSON",
            reason,
        )
        self.assertEqual("America/Chicago", timezone.key)


class AtomicWriteTests(unittest.TestCase):
    def test_replace_failure_leaves_no_partial_destination(self):
        target = Path(__file__).parent / "fixtures/atomic-write-target.md"
        pending_paths = []
        target.write_text("old content", encoding="utf-8")

        def fail_replace(source, destination):
            pending_paths.append(Path(source))
            raise OSError("replace failed")

        try:
            with mock.patch.object(krisp.os, "replace", side_effect=fail_replace):
                with self.assertRaises(OSError):
                    krisp.atomic_write(target, "new content")
            self.assertEqual("old content", target.read_text(encoding="utf-8"))
            self.assertEqual(1, len(pending_paths))
            self.assertEqual(target.parent, pending_paths[0].parent)
            self.assertNotEqual(target, pending_paths[0])
            self.assertFalse(pending_paths[0].exists())
        finally:
            try:
                target.unlink()
            except FileNotFoundError:
                pass

    def test_each_write_uses_unique_sibling_file(self):
        target = Path(__file__).parent / "fixtures/atomic-write-target.md"
        pending_paths = []
        real_replace = krisp.os.replace

        def record_replace(source, destination):
            pending_paths.append(Path(source))
            return real_replace(source, destination)

        try:
            with mock.patch.object(krisp.os, "replace", side_effect=record_replace):
                krisp.atomic_write(target, "first")
                krisp.atomic_write(target, "second")
            self.assertEqual("second", target.read_text(encoding="utf-8"))
            self.assertEqual(2, len(set(pending_paths)))
            self.assertTrue(all(path.parent == target.parent for path in pending_paths))
        finally:
            try:
                target.unlink()
            except FileNotFoundError:
                pass


class ExistingAttributionTests(unittest.TestCase):
    def test_existing_transcript_without_matching_index_is_untrusted(self):
        vault = Path(__file__).parent / "fixtures/vault"
        existing = vault / "one-one/jfuchs/2026-07-30 10.00.00 Jason _ David 1_1.md"
        meeting = {"meeting_id": "abc123"}
        current = krisp.attribution(event("David Poll"), ["Jason More", "David Poll"])
        result = krisp.existing_attribution(vault, existing, meeting, current, {"meetings": {}})
        self.assertFalse(result["exact_speaker_set_match"])
        self.assertIn(
            "existing transcript not refreshed after Krisp label changes",
            result["attribution_rejection_reasons"],
        )

    def test_existing_transcript_with_matching_index_keeps_trust(self):
        vault = Path(__file__).parent / "fixtures/vault"
        existing = vault / "one-one/jfuchs/2026-07-30 10.00.00 Jason _ David 1_1.md"
        meeting = {"meeting_id": "abc123"}
        current = krisp.attribution(event("David Poll"), ["Jason More", "David Poll"])
        index = {
            "meetings": {
                "abc123": {
                    "path": str(existing.relative_to(vault)),
                    "workiq_speakers": current["workiq_speakers"],
                    "krisp_speakers": sorted(current["krisp_speakers"]),
                    "exact_speaker_set_match": True,
                }
            }
        }
        result = krisp.existing_attribution(vault, existing, meeting, current, index)
        self.assertTrue(result["exact_speaker_set_match"])


if __name__ == "__main__":
    unittest.main()
