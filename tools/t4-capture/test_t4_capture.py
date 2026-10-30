"""Tests for the T4 (056.004-T) `/mcp show` capture evaluator.

Run: logs/t4/venv/Scripts/python.exe -m unittest discover -s tools/t4-capture -v

The connected fixture is a real screen captured through a PTY from the exact
Copilot CLI interactive `/mcp show kbdb` command against the restored
production entry. Failure fixtures are derived from it by mutating one
CLI-visible field at a time.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

import t4_capture as t4

HERE = Path(__file__).parent
CONNECTED = (HERE / "fixtures" / "mcp_show_connected.txt").read_text(encoding="utf-8")


class ParseAndEvaluate(unittest.TestCase):
    def test_real_connected_screen_passes(self):
        parsed = t4.parse_mcp_show(CONNECTED, "kbdb")
        self.assertEqual(parsed["status"], "connected")
        self.assertTrue(parsed["server_metadata_present"])
        self.assertEqual(parsed["tool_count"], 8)
        self.assertIn("get_status", parsed["tools"])
        self.assertEqual(t4.evaluate_session(parsed), [])

    def test_failed_status_fails(self):
        screen = CONNECTED.replace('"status": "connected"', '"status": "failed"')
        failures = t4.evaluate_session(t4.parse_mcp_show(screen, "kbdb"))
        self.assertTrue(any("status" in f for f in failures), failures)

    def test_os_error_232_fails_even_when_status_connected(self):
        screen = CONNECTED + "\n The pipe is being closed. (os error 232)\n"
        failures = t4.evaluate_session(t4.parse_mcp_show(screen, "kbdb"))
        self.assertTrue(any("232" in f for f in failures), failures)

    def test_missing_server_metadata_means_not_initialized(self):
        cut = CONNECTED.split('"serverMetadata"')[0]
        failures = t4.evaluate_session(t4.parse_mcp_show(cut, "kbdb"))
        self.assertTrue(any("initialized" in f for f in failures), failures)

    def test_wrong_entry_is_refused(self):
        parsed = t4.parse_mcp_show(CONNECTED.replace("kbdb", "other"), "kbdb")
        self.assertTrue(any("entry" in f for f in t4.evaluate_session(parsed)))

    def test_missing_tools_block_fails_not_passes(self):
        # Connected + initialized text but no `tools (N)` block must not pass:
        # the advertised tool list is recorded evidence, not optional.
        screen = CONNECTED.replace("tools (8)", "tools").split("\n data")[0]
        screen += '\n data\n {\n "name": "kbdb",\n "status": "connected",\n "serverMetadata": {}\n }\n'
        failures = t4.evaluate_session(t4.parse_mcp_show(screen, "kbdb"))
        self.assertTrue(any("tool" in f for f in failures), failures)

    def test_empty_screen_fails_not_passes(self):
        failures = t4.evaluate_session(t4.parse_mcp_show("", "kbdb"))
        self.assertTrue(failures)

    def test_exit_zero_alone_is_never_a_pass(self):
        result = t4.build_session_result(
            parsed=t4.parse_mcp_show("", "kbdb"), exit_code=0
        )
        self.assertFalse(result["passed"])


class EntryIdentity(unittest.TestCase):
    def _write(self, entry):
        d = tempfile.mkdtemp(dir=os.environ.get("TEMP"))
        p = Path(d) / ".mcp.json"
        p.write_text(json.dumps({"mcpServers": {"kbdb": entry}}), encoding="utf-8")
        return p

    def _exe(self):
        d = tempfile.mkdtemp(dir=os.environ.get("TEMP"))
        p = Path(d) / "kbdb.exe"
        p.write_bytes(b"MZ")
        return str(p)

    def test_direct_delivered_entry_accepted(self):
        exe = self._exe()
        ident = t4.check_entry(self._write({"command": exe, "args": ["serve"]}), "kbdb")
        self.assertEqual(ident["command"], exe)
        self.assertEqual(len(ident["config_sha256"]), 64)

    def test_bun_shim_wrapper_refused(self):
        p = self._write(
            {"command": "bun", "args": [".copilot/graphtor-mcp-shim.cjs", "kbdb", "serve"]}
        )
        with self.assertRaises(t4.IdentityError):
            t4.check_entry(p, "kbdb")

    def test_extra_args_refused(self):
        with self.assertRaises(t4.IdentityError):
            t4.check_entry(self._write({"command": self._exe(), "args": ["serve", "--x"]}), "kbdb")

    def test_relative_or_missing_command_refused(self):
        for cmd in ("kbdb", "C:\\nope\\kbdb.exe"):
            with self.assertRaises(t4.IdentityError):
                t4.check_entry(self._write({"command": cmd, "args": ["serve"]}), "kbdb")

    def test_non_kbdb_executable_refused(self):
        d = tempfile.mkdtemp(dir=os.environ.get("TEMP"))
        other = Path(d) / "node.exe"
        other.write_bytes(b"MZ")
        with self.assertRaises(t4.IdentityError):
            t4.check_entry(self._write({"command": str(other), "args": ["serve"]}), "kbdb")


class ServerProcessCorrelation(unittest.TestCase):
    EXE = "C:\\w\\.kbdb\\bin\\kbdb.exe"

    def test_direct_child_selected(self):
        procs = [
            {"pid": 10, "ppid": 1, "exe": "C:\\Tools\\copilot.exe"},
            {"pid": 11, "ppid": 10, "exe": self.EXE.upper()},
        ]
        self.assertEqual(t4.select_server_process(procs, 10, self.EXE)["pid"], 11)

    def test_intermediate_wrapper_refused(self):
        procs = [
            {"pid": 10, "ppid": 1, "exe": "C:\\Tools\\copilot.exe"},
            {"pid": 12, "ppid": 10, "exe": "C:\\bun.exe"},
            {"pid": 13, "ppid": 12, "exe": self.EXE},
        ]
        with self.assertRaises(t4.IdentityError):
            t4.select_server_process(procs, 10, self.EXE)

    def test_no_server_process_refused(self):
        procs = [{"pid": 10, "ppid": 1, "exe": "C:\\Tools\\copilot.exe"}]
        with self.assertRaises(t4.IdentityError):
            t4.select_server_process(procs, 10, self.EXE)

    def test_unrelated_kbdb_from_another_client_is_ignored(self):
        procs = [
            {"pid": 10, "ppid": 1, "exe": "C:\\Tools\\copilot.exe"},
            {"pid": 20, "ppid": 2, "exe": "C:\\pwsh.exe"},
            {"pid": 21, "ppid": 20, "exe": self.EXE},
            {"pid": 11, "ppid": 10, "exe": self.EXE},
        ]
        self.assertEqual(t4.select_server_process(procs, 10, self.EXE)["pid"], 11)

    def test_only_unrelated_kbdb_is_still_refused(self):
        procs = [
            {"pid": 10, "ppid": 1, "exe": "C:\\Tools\\copilot.exe"},
            {"pid": 21, "ppid": 20, "exe": self.EXE},
        ]
        with self.assertRaises(t4.IdentityError):
            t4.select_server_process(procs, 10, self.EXE)


if __name__ == "__main__":
    unittest.main()
