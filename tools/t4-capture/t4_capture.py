"""T4 (056.004-T) restored-production `/mcp show` capture and evaluator.

Drives the EXACT interactive Copilot CLI executable inside a PTY (client
terminal capture -- it is not an MCP server wrapper and never alters the
server command, config, or environment), types the real `/mcp show <entry>`
slash command, reconstructs the visible screen with a VT parser, and
evaluates ONLY the fields that screen exposes. Process logs are never parsed
or substituted. No model prompt is ever sent.
"""
import argparse
import ctypes
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

SCROLLBAR = "\u2503"
WRAPPER_COMMANDS = {
    "bun", "bunx", "node", "npx", "python", "python3", "pwsh", "powershell",
    "cmd", "sh", "bash", "deno",
}


class IdentityError(Exception):
    """The production entry or the spawned process is not the delivered one."""


# --------------------------------------------------------------- screen parse
def _clean(screen_text):
    lines = []
    for raw in screen_text.splitlines():
        line = raw.replace(SCROLLBAR, "").rstrip()
        lines.append(line)
    return lines


def parse_mcp_show(screen_text, expected_entry):
    """Extract the CLI-visible `/mcp show` fields from a reconstructed screen."""
    lines = _clean(screen_text)
    text = "\n".join(lines)
    header = re.search(r"MCP \u00b7 (\S+)", text)
    status = re.search(r'"status":\s*"([^"]*)"', text)
    count = re.search(r"tools \((\d+)\)", text)
    tools = []
    in_tools = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"tools \(\d+\)", stripped):
            in_tools = True
            continue
        if in_tools and stripped == "data":
            break
        match = re.match(r"^([a-z][a-z0-9_]*): ", stripped)
        if in_tools and match and not line.startswith("  "):
            tools.append(match.group(1))
    return {
        "expected_entry": expected_entry,
        "entry": header.group(1) if header else None,
        "status": status.group(1) if status else None,
        "source": (re.search(r'"source":\s*"([^"]*)"', text) or [None, None])[1],
        "server_metadata_present": '"serverMetadata"' in text,
        "tool_count": int(count.group(1)) if count else None,
        "tools": tools,
        "os_error_232": bool(re.search(r"(?i)os error 232|error 232", text)),
        "failed_signature": bool(re.search(r"(?i)failed to (start|connect)|connection failed", text)),
    }


def mcp_show_rendered(screen_text):
    """True once the `/mcp show` screen has fully rendered its data and tools blocks.

    The advertised tool count must equal the number of tool rows already drawn, so a
    partially drawn list keeps the capture waiting instead of being saved.
    """
    text = "\n".join(_clean(screen_text))
    if "esc back" not in text or '"status"' not in text:
        return False
    parsed = parse_mcp_show(screen_text, "")
    if parsed["tool_count"] is None or len(parsed["tools"]) != parsed["tool_count"]:
        return False
    # The trailing `data` JSON block must be drawn with every NESTED object closed.
    # The real screen clips the outermost closing brace at the viewport bottom, so
    # depth <= 1 is complete; a nested object still open is a partial frame. A
    # rendered failure state is captured too (and then fails evaluation).
    lines = _clean(screen_text)
    start = next((i for i, line in enumerate(lines) if line.strip() == "data"), None)
    if start is None:
        return False
    block = "\n".join(lines[start + 1:]).split("esc back")[0]
    depth = block.count("{") - block.count("}")
    return block.count("{") > 0 and depth <= 1


def wait_for_stable(get_text, predicate, timeout, settle,
                    sleep=time.sleep, monotonic=time.monotonic):
    """Return the screen text once `predicate` holds and the text stopped changing.

    The text must be identical across `settle` seconds, so a frame that is still
    being drawn is never captured. Returns None on timeout.
    """
    deadline = monotonic() + timeout
    last = None
    since = None
    while monotonic() < deadline:
        text = get_text()
        if predicate(text):
            if text == last:
                if monotonic() - since >= settle:
                    return text
            else:
                last, since = text, monotonic()
        else:
            last = since = None
        sleep(0.25)
    return None


def evaluate_session(parsed):
    """Return the list of acceptance failures for one parsed `/mcp show` screen."""
    failures = []
    if parsed["entry"] != parsed["expected_entry"]:
        failures.append(
            f"entry mismatch: screen shows {parsed['entry']!r}, expected {parsed['expected_entry']!r}"
        )
    if parsed["status"] != "connected":
        failures.append(f"status is {parsed['status']!r}, expected 'connected'")
    if not parsed["server_metadata_present"]:
        failures.append("server not shown as initialized: no serverMetadata in the screen")
    if parsed["os_error_232"]:
        failures.append("OS error 232 signature present")
    if parsed["failed_signature"]:
        failures.append("failed-connection signature present")
    if parsed["tool_count"] is None or not parsed["tools"]:
        failures.append("advertised tool list missing from the /mcp show screen")
    elif parsed["tool_count"] != len(parsed["tools"]):
        failures.append(
            f"tool list incomplete: header says {parsed['tool_count']}, parsed {len(parsed['tools'])}"
        )
    return failures


def build_session_result(parsed, exit_code):
    """Exit code alone is never a pass: the screen evaluation decides."""
    failures = evaluate_session(parsed)
    return {
        "passed": not failures,
        "failures": failures,
        "client_exit_code": exit_code,
        "status": parsed["status"],
        "tool_count": parsed["tool_count"],
        "tools": parsed["tools"],
    }


# ------------------------------------------------------------ entry identity
def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_entry(mcp_json_path, entry_name):
    """Refuse anything but the direct delivered `kbdb serve` entry."""
    path = Path(mcp_json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    entry = data.get("mcpServers", {}).get(entry_name)
    if not isinstance(entry, dict):
        raise IdentityError(f"entry {entry_name!r} not found in {path.name}")
    command = entry.get("command")
    args = entry.get("args")
    if not isinstance(command, str) or not os.path.isabs(command):
        raise IdentityError("entry command must be an absolute path to the delivered binary")
    base = os.path.basename(command).lower()
    if base in {name + ".exe" for name in WRAPPER_COMMANDS} | WRAPPER_COMMANDS:
        raise IdentityError(f"entry command {base!r} is an interpreter/wrapper")
    if base not in ("kbdb", "kbdb.exe"):
        raise IdentityError(f"entry command {base!r} is not the kbdb executable")
    if not Path(command).is_file():
        raise IdentityError("entry command does not exist")
    if args != ["serve"]:
        raise IdentityError(f"entry args must be exactly ['serve'], got {args!r}")
    return {
        "config_path": str(path),
        "config_sha256": sha256_file(path),
        "command": command,
        "args": args,
        "exe_sha256": sha256_file(command),
        "entry_projection_sha256": hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def select_server_process(procs, copilot_pid, expected_exe):
    """Pick the Copilot-spawned server; refuse wrappers and missing servers."""
    by_pid = {p["pid"]: p for p in procs}
    want = expected_exe.lower()
    for proc in procs:
        if (proc.get("exe") or "").lower() != want:
            continue
        # Ancestor chain (nearest first), bounded against cycles.
        chain = []
        cursor = by_pid.get(proc["ppid"])
        while cursor is not None and len(chain) < 64:
            chain.append(cursor)
            if cursor["pid"] == copilot_pid:
                break
            cursor = by_pid.get(cursor["ppid"])
        if not chain or chain[-1]["pid"] != copilot_pid:
            continue  # not a descendant of THIS Copilot session (another client's server)
        # Only Copilot's own re-exec may sit between it and the server.
        for between in chain[:-1]:
            if os.path.basename((between.get("exe") or "").lower()) != "copilot.exe":
                raise IdentityError(
                    f"server pid {proc['pid']} is not a direct Copilot child: "
                    f"intermediate process {between.get('exe')!r}"
                )
        return proc
    raise IdentityError("no Copilot-spawned process runs the delivered kbdb executable")


# ------------------------------------------------------------- OS evidence
def process_table():
    cmd = (
        "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,"
        "ExecutablePath,@{n='Created';e={$_.CreationDate.ToUniversalTime().ToString('o')}} "
        "| ConvertTo-Json -Compress"
    )
    out = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=60, check=False,
    )
    if out.returncode != 0:
        raise IdentityError(f"process table query failed (exit {out.returncode})")
    rows = json.loads(out.stdout)
    return [
        {"pid": r["ProcessId"], "ppid": r["ParentProcessId"],
         "exe": r["ExecutablePath"], "created": r["Created"]}
        for r in (rows if isinstance(rows, list) else [rows])
    ]


def parse_utc(text):
    """Parse an ISO-8601 UTC timestamp, tolerating 7-digit fractional seconds."""
    cleaned = re.sub(r"(\.\d{6})\d+", r"\1", text.strip().replace("Z", "+00:00"))
    value = datetime.fromisoformat(cleaned)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


_EPOCH_1601 = datetime(1601, 1, 1, tzinfo=timezone.utc)


def utc_ticks(text):
    """Exact 100 ns ticks since 1601-01-01 UTC (FILETIME units) for an ISO UTC string.

    Both the CIM creation string (7 fractional digits) and a FILETIME are expressed
    in these ticks, so process creation identities compare with integer equality.
    """
    match = re.search(r"\.(\d+)", text)
    fraction = (match.group(1) + "0000000")[:7] if match else "0000000"
    whole = parse_utc(re.sub(r"\.\d+", "", text))
    seconds = int((whole - _EPOCH_1601).total_seconds())
    return seconds * 10_000_000 + int(fraction)


_K32 = ctypes.WinDLL("kernel32", use_last_error=True)
_NT = ctypes.WinDLL("ntdll")
_K32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_K32.OpenProcess.restype = wintypes.HANDLE
_K32.CloseHandle.argtypes = [wintypes.HANDLE]
_NT.NtQueryInformationProcess.argtypes = [
    wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]
_K32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
_K32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_K32.WaitForSingleObject.restype = wintypes.DWORD
_K32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
_K32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
_K32.ReadProcessMemory.argtypes = [
    wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t)]
_PROCESS_TERMINATE = 0x0001
_PROCESS_VM_READ = 0x0010
_PROCESS_QUERY_INFORMATION = 0x0400
_SYNCHRONIZE = 0x00100000
_WAIT_OBJECT_0 = 0


class OwnedProcess:
    """A verified OS process HANDLE for the Copilot-spawned server.

    The handle is opened once, immediately after the process is identified from
    the process table, and is then verified against the recorded executable path
    and creation time. While it is held the OS cannot reuse that process's PID,
    so every later query and the termination act on THAT process object, never
    on whatever a PID number happens to name later. Opening fails closed when
    the identity cannot be proven, and nothing is terminated in that case.
    """

    def __init__(self, handle, pid):
        self._handle = handle
        self.pid = pid

    @classmethod
    def open(cls, pid, expected_exe, expected_created_utc):
        access = _PROCESS_TERMINATE | _SYNCHRONIZE | _PROCESS_QUERY_INFORMATION | _PROCESS_VM_READ
        handle = _K32.OpenProcess(access, False, pid)
        if not handle:
            raise IdentityError(f"cannot open pid {pid} (error {ctypes.get_last_error()})")
        owned = cls(handle, pid)
        try:
            owned._verify(expected_exe, expected_created_utc)
        except BaseException:
            owned.close()
            raise
        return owned

    def _verify(self, expected_exe, expected_created_utc):
        size = wintypes.DWORD(32768)
        buf = ctypes.create_unicode_buffer(size.value)
        if not _K32.QueryFullProcessImageNameW(self._handle, 0, buf, ctypes.byref(size)):
            raise IdentityError(f"cannot read the image name of pid {self.pid}")
        if os.path.normcase(os.path.normpath(buf.value)) != os.path.normcase(os.path.normpath(expected_exe)):
            raise IdentityError(f"pid {self.pid} runs {buf.value!r}, not the delivered executable")
        created = self._creation_ticks()
        expected = utc_ticks(expected_created_utc)
        # The CIM string and the FILETIME share microsecond precision only (the
        # CIM sub-microsecond digit is always 0); compare as exact integers there.
        if created // 10 != expected // 10:
            raise IdentityError(
                f"pid {self.pid} creation ticks {created} do not match the recorded "
                f"{expected} at microsecond precision (the PID may have been reused)"
            )

    def _creation_ticks(self):
        creation, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
        if not _K32.GetProcessTimes(self._handle, creation, exited, kernel, user):
            raise IdentityError(f"cannot read the creation time of pid {self.pid}")
        return (creation.dwHighDateTime << 32) | creation.dwLowDateTime  # 100 ns since 1601

    def _require_open(self):
        if self._handle is None:
            raise IdentityError(f"process handle for pid {self.pid} is closed")

    def is_running(self):
        self._require_open()
        return _K32.WaitForSingleObject(self._handle, 0) != _WAIT_OBJECT_0

    def wait_exit(self, seconds):
        """True when the owned process has exited within `seconds`."""
        self._require_open()
        return _K32.WaitForSingleObject(self._handle, int(seconds * 1000)) == _WAIT_OBJECT_0

    def terminate(self):
        """Terminate exactly this process object; failures surface."""
        self._require_open()
        if not self.is_running():
            return
        if not _K32.TerminateProcess(self._handle, 1):
            raise IdentityError(f"TerminateProcess failed for pid {self.pid} (error {ctypes.get_last_error()})")

    def cwd(self):
        """Current directory of the owned process, read from its PEB."""
        self._require_open()
        pbi = (ctypes.c_size_t * 6)()
        ret = wintypes.ULONG()
        if _NT.NtQueryInformationProcess(self._handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(ret)):
            raise IdentityError("NtQueryInformationProcess failed")

        def read(addr, size):
            buf = (ctypes.c_char * size)()
            got = ctypes.c_size_t()
            if not _K32.ReadProcessMemory(self._handle, ctypes.c_void_p(addr), buf, size, ctypes.byref(got)):
                raise IdentityError("ReadProcessMemory failed")
            return buf.raw

        params = int.from_bytes(read(pbi[1] + 0x20, 8), "little")
        length = int.from_bytes(read(params + 0x38, 2), "little")
        buffer = int.from_bytes(read(params + 0x40, 8), "little")
        return read(buffer, length).decode("utf-16-le").rstrip("\\")

    def close(self):
        if self._handle is not None:
            _K32.CloseHandle(self._handle)
            self._handle = None


def teardown_confirmed(table, client_pid, server_pid):
    """True only when neither the Copilot client nor its server is still running."""
    live = {p["pid"] for p in table}
    if client_pid in live:
        return False
    return server_pid is None or server_pid not in live


def copilot_identity(copilot_exe):
    out = subprocess.run([copilot_exe, "--version"], capture_output=True, text=True, timeout=30, check=False)
    if out.returncode != 0:
        raise IdentityError(f"copilot --version exited {out.returncode}")
    return {
        "exe": copilot_exe,
        "sha256": sha256_file(copilot_exe),
        "version": out.stdout.strip().splitlines()[0],
    }


# ------------------------------------------------------------------- capture
def capture_session(copilot_exe, workspace, entry, expected_exe, rows=50, cols=160):
    """Run ONE interactive Copilot session and capture the real `/mcp show` screen."""
    import pyte
    from winpty import PtyProcess

    class Screen(pyte.Screen):
        # Terminal queries (DSR/DA) are not answered; ignore pyte's private-arg bug.
        def report_device_status(self, *a, **k):
            pass

        def report_device_attributes(self, *a, **k):
            pass

    screen = Screen(cols, rows)
    stream = pyte.Stream(screen)
    lock = threading.Lock()
    proc = PtyProcess.spawn([copilot_exe], cwd=workspace, dimensions=(rows, cols))
    stop = threading.Event()

    def pump():
        while not stop.is_set() and proc.isalive():
            try:
                data = proc.read(4096)
            except EOFError:
                return
            if data:
                with lock:
                    stream.feed(data)

    threading.Thread(target=pump, daemon=True).start()

    def text():
        with lock:
            return "\n".join(line.rstrip() for line in screen.display)

    def wait_for(predicate, timeout):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if predicate(text()):
                return True
            time.sleep(0.5)
        return False

    record = {"started_utc": datetime.now(timezone.utc).isoformat(), "copilot_pid": proc.pid}
    owned_server = None
    try:
        if not wait_for(lambda t: "/ commands" in t or "\u276f" in t, 60):
            raise IdentityError("Copilot interactive prompt never appeared")
        proc.write("/mcp show " + entry + "\r")
        screen_text = wait_for_stable(text, mcp_show_rendered, 45, 2.0)
        if screen_text is None:
            raise IdentityError("/mcp show screen never rendered completely and settled")
        record["captured_utc"] = datetime.now(timezone.utc).isoformat()
        table = process_table()
        server = select_server_process(table, proc.pid, expected_exe)
        # Retain a verified OS handle to the server NOW, so cleanup never acts
        # on a bare PID that could be reused by another client's process.
        try:
            owned_server = OwnedProcess.open(server["pid"], expected_exe, server["created"])
        except IdentityError as err:
            # Fail closed and make the unclean state visible: the identified server
            # is NOT terminated (ownership is unproven) and may still be running.
            raise IdentityError(
                f"{err}; server pid {server['pid']} was left running unowned and was not terminated"
            ) from err
        record["server"] = {
            "pid": server["pid"], "ppid": server["ppid"], "exe": server["exe"],
            "exe_sha256": sha256_file(server["exe"]), "created_utc": server["created"],
            "cwd": owned_server.cwd(),
            "evidence_source": "Win32_Process table + verified process handle (PEB read) of the Copilot-spawned child",
        }
        record["screen_text"] = screen_text
    finally:
        stop.set()
        try:
            proc.write("\x1b")
            time.sleep(0.5)
            proc.write("\x03")
            time.sleep(0.5)
            proc.write("\x03")
            time.sleep(2)
        except Exception:
            pass
        if proc.isalive():
            try:
                proc.terminate(force=True)
            except (PermissionError, OSError):
                time.sleep(2)  # the child is already exiting; confirm below
        record["client_exit_code"] = proc.exitstatus
        record["client_still_alive"] = proc.isalive()
        # Owned-child cleanup: only through the verified handle. A server that
        # does not exit with its client is terminated by that handle (never by
        # PID); any failure leaves teardown unconfirmed.
        server_gone = owned_server is None
        if owned_server is not None:
            try:
                if not owned_server.wait_exit(5):
                    owned_server.terminate()
                server_gone = owned_server.wait_exit(10)
            except IdentityError as err:
                record["server_cleanup_error"] = str(err)
            finally:
                owned_server.close()
        time.sleep(1)
        record["teardown_confirmed"] = bool(
            server_gone and teardown_confirmed(process_table(), proc.pid, None)
        )
    return record


def run(args):
    workspace = os.path.normcase(os.path.realpath(args.workspace))
    ident = check_entry(Path(workspace) / ".mcp.json", args.entry)
    client = copilot_identity(args.copilot_exe)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sessions = []
    teardown_failed = False
    for index in range(args.sessions):
        # The config must not drift between sessions.
        again = check_entry(Path(workspace) / ".mcp.json", args.entry)
        if again["config_sha256"] != ident["config_sha256"]:
            raise IdentityError("production config changed between sessions")
        record = capture_session(args.copilot_exe, workspace, args.entry, ident["command"])
        parsed = parse_mcp_show(record["screen_text"], args.entry)
        result = build_session_result(parsed, record["client_exit_code"])
        server = record["server"]
        if server["exe_sha256"] != ident["exe_sha256"]:
            result["failures"].append("spawned server exe hash differs from the entry's exe hash")
        if os.path.normcase(server["cwd"]) != workspace:
            result["failures"].append(
                f"server cwd {server['cwd']!r} is not the canonical workspace"
            )
        result["passed"] = not result["failures"]
        teardown_ok = record.get("teardown_confirmed", False)
        if not teardown_ok:
            result["failures"].append("client/server teardown could not be confirmed")
            result["passed"] = False
        screen_file = out_dir / f"session{index + 1}.screen.txt"
        screen_file.write_text(record["screen_text"], encoding="utf-8")
        sessions.append({
            "index": index + 1,
            "started_utc": record["started_utc"],
            "captured_utc": record["captured_utc"],
            "diagnostic_gate": "off",
            "copilot_pid": record["copilot_pid"],
            "server": server,
            "screen_file": str(screen_file),
            "screen_fields": parsed,
            "result": result,
        })
        if not teardown_ok:
            teardown_failed = True
            break  # withhold further sessions while processes may still overlap
    summary = {
        "copilot": client,
        "config": ident,
        "workspace": workspace,
        "sessions": sessions,
        "teardown_failed": teardown_failed,
        "all_passed": len(sessions) == args.sessions and all(s["result"]["passed"] for s in sessions),
    }
    (out_dir / "sessions.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--copilot-exe", required=True)
    parser.add_argument("--entry", default="kbdb")
    parser.add_argument("--sessions", type=int, default=3)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    try:
        summary = run(args)
    except IdentityError as err:
        print(f"T4_REFUSED: {err}", file=sys.stderr)
        return 3
    print(json.dumps({"all_passed": summary["all_passed"],
                      "sessions": [s["result"]["passed"] for s in summary["sessions"]]}))
    if summary["teardown_failed"]:
        return 4
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
