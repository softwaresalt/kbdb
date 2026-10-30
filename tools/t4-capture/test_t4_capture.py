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


class OwnedProcessTests(unittest.TestCase):
    """OS-boundary tests using only processes this test owns (a real `ping.exe`).

    No unrelated process is ever touched: PID-reuse is simulated by presenting
    a live owned process with a DIFFERENT expected creation identity.
    """

    @classmethod
    def setUpClass(cls):
        import shutil
        cls.ping = shutil.which("ping.exe")
        if cls.ping is None:
            raise unittest.SkipTest("ping.exe not available")

    def setUp(self):
        import subprocess
        self.child = subprocess.Popen(
            [self.ping, "-n", "60", "127.0.0.1"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self.addCleanup(self._reap)
        row = [p for p in t4.process_table() if p["pid"] == self.child.pid]
        self.assertEqual(len(row), 1)
        self.row = row[0]

    def _reap(self):
        if self.child.poll() is None:
            self.child.kill()
        self.child.wait(timeout=10)

    def test_verified_owned_handle_terminates_exactly_that_process(self):
        owned = t4.OwnedProcess.open(self.child.pid, self.row["exe"], self.row["created"])
        try:
            self.assertTrue(owned.is_running())
            owned.terminate()
            self.child.wait(timeout=10)
            self.assertFalse(owned.is_running())
        finally:
            owned.close()

    def test_same_exe_different_creation_identity_is_refused_and_not_terminated(self):
        # Simulates PID reuse by another client's process with the same exe.
        from datetime import timedelta
        created = t4.parse_utc(self.row["created"])
        wrong = (created + timedelta(hours=1)).isoformat()
        with self.assertRaises(t4.IdentityError):
            t4.OwnedProcess.open(self.child.pid, self.row["exe"], wrong)
        self.assertIsNone(self.child.poll(), "refused open must never terminate the process")

    def test_creation_time_mismatch_inside_the_old_50ms_window_is_refused(self):
        # Exact 100 ns identity: even a 10 ms difference is a different process.
        from datetime import timedelta
        wrong = (t4.parse_utc(self.row["created"]) + timedelta(milliseconds=10)).isoformat()
        with self.assertRaises(t4.IdentityError):
            t4.OwnedProcess.open(self.child.pid, self.row["exe"], wrong)
        self.assertIsNone(self.child.poll())

    def test_ticks_parse_keeps_seven_digit_cim_precision(self):
        base = t4.utc_ticks("2026-10-30T21:35:13.0147680Z")
        self.assertEqual(t4.utc_ticks("2026-10-30T21:35:13.0147681Z") - base, 1)
        self.assertEqual(t4.utc_ticks("2026-10-30T21:35:13.014768Z"), base)

    def test_different_exe_is_refused_and_not_terminated(self):
        with self.assertRaises(t4.IdentityError):
            t4.OwnedProcess.open(self.child.pid, "C:\\other\\kbdb.exe", self.row["created"])
        self.assertIsNone(self.child.poll())

    def test_unopenable_pid_fails_closed(self):
        with self.assertRaises(t4.IdentityError):
            t4.OwnedProcess.open(0x7FFFFFF0, self.row["exe"], self.row["created"])

    def test_terminate_on_a_closed_handle_surfaces_instead_of_succeeding(self):
        owned = t4.OwnedProcess.open(self.child.pid, self.row["exe"], self.row["created"])
        owned.close()
        with self.assertRaises(t4.IdentityError):
            owned.terminate()
        self.assertIsNone(self.child.poll())


class RenderReadiness(unittest.TestCase):
    def test_fully_rendered_screen_is_ready(self):
        self.assertTrue(t4.mcp_show_rendered(CONNECTED))

    def test_status_block_without_tools_header_is_not_ready_yet(self):
        # A partially rendered screen must keep waiting rather than be captured.
        partial = CONNECTED.replace("tools (8)", "tools")
        self.assertFalse(t4.mcp_show_rendered(partial))

    def test_all_tools_but_unfinished_data_block_is_not_ready(self):
        # Complete tool rows and footer, but a nested data object is still open.
        head = CONNECTED.split('"instructions"')[0]
        partial = head + '\n esc back \u00b7 q close\n'
        self.assertFalse(t4.mcp_show_rendered(partial))

    def test_real_screen_with_clipped_outer_brace_is_ready(self):
        # The captured real screen never draws the outermost closing brace.
        self.assertTrue(t4.mcp_show_rendered(CONNECTED))
        data = CONNECTED.split("\n data")[1]
        self.assertEqual(data.count("{") - data.count("}"), 1)

    def test_stable_wait_returns_the_settled_frame(self):
        frames = iter(["draw1", "draw2", "final", "final", "final", "final", "final"])
        state = {"last": "draw1", "t": 0.0}

        def get_text():
            state["last"] = next(frames, state["last"])
            return state["last"]

        def sleep(seconds):
            state["t"] += seconds

        out = t4.wait_for_stable(get_text, lambda t: True, timeout=30, settle=1.0,
                                 sleep=sleep, monotonic=lambda: state["t"])
        self.assertEqual(out, "final")

    def test_stable_wait_never_returns_a_changing_frame(self):
        counter = {"n": 0, "t": 0.0}

        def get_text():
            counter["n"] += 1
            return f"frame{counter['n']}"

        def sleep(seconds):
            counter["t"] += seconds

        out = t4.wait_for_stable(get_text, lambda t: True, timeout=5, settle=1.0,
                                 sleep=sleep, monotonic=lambda: counter["t"])
        self.assertIsNone(out)

    def test_stable_wait_times_out_when_predicate_never_holds(self):
        clock = {"t": 0.0}
        out = t4.wait_for_stable(lambda: "x", lambda t: False, timeout=3, settle=1.0,
                                 sleep=lambda s: clock.__setitem__("t", clock["t"] + s),
                                 monotonic=lambda: clock["t"])
        self.assertIsNone(out)

    def test_fully_rendered_failure_state_is_ready(self):
        # A rendered failure must still be captured (and then fail evaluation).
        failed = CONNECTED.replace('"status": "connected"', '"status": "failed"')
        self.assertTrue(t4.mcp_show_rendered(failed))

    def test_header_present_but_tool_list_incomplete_is_not_ready(self):
        lines = [l for l in CONNECTED.splitlines()
                 if not l.lstrip().startswith(("get_status:", "list_sources:"))]
        self.assertFalse(t4.mcp_show_rendered("\n".join(lines)))

    def test_tools_header_without_status_block_is_not_ready(self):
        partial = CONNECTED.replace('"status"', '"stat"')
        self.assertFalse(t4.mcp_show_rendered(partial))


class Teardown(unittest.TestCase):
    def test_confirmed_only_when_both_pids_gone(self):
        table = [{"pid": 1, "ppid": 0, "exe": "x"}]
        self.assertTrue(t4.teardown_confirmed(table, client_pid=10, server_pid=11))

    def test_live_client_or_server_is_not_confirmed(self):
        for alive in (10, 11):
            table = [{"pid": alive, "ppid": 0, "exe": "x"}]
            self.assertFalse(t4.teardown_confirmed(table, client_pid=10, server_pid=11))

    def test_unknown_server_pid_still_checks_client(self):
        self.assertFalse(
            t4.teardown_confirmed([{"pid": 10, "ppid": 0, "exe": "x"}], client_pid=10, server_pid=None)
        )


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
