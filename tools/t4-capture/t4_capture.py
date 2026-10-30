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


def process_cwd(pid):
    """Read a child's current directory from its PEB (own descendant, same user)."""
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    nt = ctypes.WinDLL("ntdll")
    k32.OpenProcess.restype = wintypes.HANDLE
    handle = k32.OpenProcess(0x0400 | 0x0010, False, pid)  # QUERY_INFORMATION | VM_READ
    if not handle:
        raise IdentityError(f"cannot open pid {pid} to read its cwd")
    try:
        pbi = (ctypes.c_size_t * 6)()
        ret = wintypes.ULONG()
        if nt.NtQueryInformationProcess(handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(ret)):
            raise IdentityError("NtQueryInformationProcess failed")
        peb = pbi[1]

        def read(addr, size):
            buf = (ctypes.c_char * size)()
            got = ctypes.c_size_t()
            if not k32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, size, ctypes.byref(got)):
                raise IdentityError("ReadProcessMemory failed")
            return buf.raw

        params = int.from_bytes(read(peb + 0x20, 8), "little")
        length = int.from_bytes(read(params + 0x38, 2), "little")
        buffer = int.from_bytes(read(params + 0x40, 8), "little")
        return read(buffer, length).decode("utf-16-le").rstrip("\\")
    finally:
        k32.CloseHandle(handle)


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
    try:
        if not wait_for(lambda t: "/ commands" in t or "\u276f" in t, 60):
            raise IdentityError("Copilot interactive prompt never appeared")
        proc.write("/mcp show " + entry + "\r")
        if not wait_for(lambda t: "esc back" in t and '"status"' in t, 45):
            raise IdentityError("/mcp show screen never rendered a status block")
        record["captured_utc"] = datetime.now(timezone.utc).isoformat()
        screen_text = text()
        table = process_table()
        server = select_server_process(table, proc.pid, expected_exe)
        record["server"] = {
            "pid": server["pid"], "ppid": server["ppid"], "exe": server["exe"],
            "exe_sha256": sha256_file(server["exe"]), "created_utc": server["created"],
            "cwd": process_cwd(server["pid"]),
            "evidence_source": "Win32_Process table + PEB read of the Copilot-spawned child",
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
        # Own-child cleanup: the recorded server pid, only if it still runs the
        # delivered executable (never a name-based or unrelated kill).
        server = record.get("server")
        if server:
            time.sleep(1)
            still = [p for p in process_table() if p["pid"] == server["pid"]]
            if still and (still[0].get("exe") or "").lower() == expected_exe.lower():
                subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                     f"Stop-Process -Id {int(server['pid'])} -Force"],
                    capture_output=True, timeout=30, check=False,
                )
    return record


def run(args):
    workspace = os.path.normcase(os.path.realpath(args.workspace))
    ident = check_entry(Path(workspace) / ".mcp.json", args.entry)
    client = copilot_identity(args.copilot_exe)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sessions = []
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
    summary = {
        "copilot": client,
        "config": ident,
        "workspace": workspace,
        "sessions": sessions,
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
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
