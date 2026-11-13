# File Integrity Monitor (FIM)

A command-line tool for Linux that detects unauthorized changes to a protected folder. It takes a trusted snapshot (a **baseline**) of every file, signs it, and later reports files that were **added**, **deleted**, **content-modified** or had their **permissions changed**. It can run on demand, continuously in real time, and on a schedule.

Built in Python on Kali Linux (VMware). It was tested with dummy data only. Do not use it to protect real sensitive files without reviewing the [known limitations](#known-limitations) first.

---

## Table of contents

1. [Features](#features)
2. [Threat model](#threat-model)
3. [How it works](#how-it-works)
4. [Project structure](#project-structure)
5. [Requirements and installation](#requirements-and-installation)
6. [Command reference](#command-reference)
7. [Quick start](#quick-start)
8. [Example output](#example-output)
9. [Log format and log verification](#log-format-and-log-verification)
10. [Real-time monitoring](#real-time-monitoring)
11. [Running as a systemd service](#running-as-a-systemd-service)
12. [Scheduled scans with cron](#scheduled-scans-with-cron)
13. [Exit codes](#exit-codes)
14. [Security design](#security-design)
15. [Known limitations](#known-limitations)
16. [Attack testing](#attack-testing)
17. [References](#references)

---

## Features

- **SHA-256 hashing**, read in chunks so large files never fill memory
- **Recursive scanning** of a protected folder and all its subfolders
- **Rich baseline:** hash, permission string, owner, group, size and timestamps for every file
- **Four change types detected:** added, deleted, content modified, permissions changed
- **Signed baseline:** the baseline file is protected with an **HMAC-SHA256** signature and a per-folder secret key
- **Tamper-evident log:** each log entry is chained to the previous one with SHA-256, and a verify command finds edited or removed entries
- **Real-time monitoring** with `watchdog` (inotify), with duplicate-event debouncing
- **Summary mode** (`--check`) and **detailed mode** (`--stat`) reports
- **Confirmation prompt** before the baseline is replaced (`--update`)
- **Exit codes** so cron, services and scripts can react to results
- Deployable as a **systemd service** plus a **cron** scheduled scan

---

## Threat model

**Attacker:** someone with ordinary user-level access to the machine who can edit, add or delete files in the protected folder, and who then tries to hide it by editing the baseline, the signature, or the logs.

| Change | How it is detected |
|---|---|
| File content modified | SHA-256 hash differs from the baseline |
| File added | Path exists now but is not in the baseline |
| File deleted | Path is in the baseline but missing now |
| Permissions changed | Stored permission string differs from the current one |
| Baseline edited | HMAC signature no longer matches (warning is shown) |
| Log entry edited or removed | Hash chain no longer matches the stored chain |

**Out of scope:** an attacker with **root** access can stop the service, remove the cron job, read the key and rewrite everything. This tool detects tampering; it cannot stop a root user.

---

## How it works

1. **`--init <folder>`** scans the folder recursively, hashes each file and records its metadata. The result is saved as `json_files/<folder>.json`. A 32-byte random key is created in `key_files/` the first time, and an HMAC-SHA256 signature of the baseline is saved in `sig_files/`. Every path found is also recorded in `paths.txt`, which is how the tool knows a folder has been initialised.
2. **`--check` / `--stat`** rescan the folder and compare the result with the baseline using set operations:
   - in the current scan only: **added**
   - in the baseline only: **deleted**
   - in both, with a different hash: **content modified**
   - in both, with a different permission string: **permissions changed**
3. **`--monitor`** starts a `watchdog` observer that reports file events as they happen and writes each one to the log.
4. **`--verify_log`** recomputes the hash chain of the log and compares it with the stored chain.
5. **`--update`** accepts the current state as the new trusted baseline, after a Y/N confirmation, and re-signs it.

---

## Project structure

```
project_file_monitor/
├── app.py                    # command-line interface and real-time monitor
├── functions.py              # scanning, comparing, reporting, log chain
├── dumper_loader_file.py     # baseline save/load, key handling, HMAC signing
├── paths.txt                 # list of initialised paths (created and chmod 600 by the tool)
├── Classified/               # example protected folder (dummy data)
├── json_files/               # one baseline per protected folder
├── key_files/                # one secret key per protected folder   (never commit)
├── sig_files/                # HMAC signature of each baseline
├── log_files/
│   ├── <folder>.log          # human-readable change log
│   └── log_json_files/       # stored hash chain for each log
└── README.md
```

---

## Requirements and installation

**Requirements**

- Linux (developed on Kali), Python 3.10 or newer
- `watchdog` (the only third-party package)
- `systemd` and `cron` if you want background and scheduled operation

**Install**

```bash
git clone https://github.com/Preethzzz-K/File_Intergrity_Monitor_Tool.git project_file_monitor
cd project_file_monitor
pip install watchdog
```

The tool expects these folders and file to exist before the first run:

```bash
mkdir -p json_files key_files sig_files log_files/log_json_files
touch paths.txt
```

Run every command **from the project folder** (the tool uses the current directory as its project path).

> **Important:** `Classified/` must sit directly inside the project folder. Some file locations (signatures, logs) are derived from the protected folder's parent directory.

---

## Command reference

Run `python3 app.py --help` at any time.

| Command | What it does |
|---|---|
| `--init <path>` | Start monitoring a folder: create the baseline, key, signature and first log entry |
| `--check <path>` | Summary report of added, deleted, modified and permission-changed files |
| `--stat <path>` | Detailed report with owner, group, size, permissions and timestamps for each affected file |
| `--update <path>` | Replace the baseline with the current state (asks for Y/N confirmation) |
| `--monitor <path>` | Real-time monitoring; runs until stopped with Ctrl+C |
| `--verify_log <path>` | Verify the integrity of that folder's log |

---

## Quick start

```bash
# 1. Start monitoring a folder
python3 app.py --init /home/kali/project_file_monitor/Classified

# 2. Change something
echo "tampered" >> Classified/Agents/Agent0.txt

# 3. See what changed
python3 app.py --check /home/kali/project_file_monitor/Classified
python3 app.py --stat  /home/kali/project_file_monitor/Classified

# 4. Watch in real time (Ctrl+C to stop)
python3 app.py --monitor /home/kali/project_file_monitor/Classified

# 5. Verify the log was not tampered with
python3 app.py --verify_log /home/kali/project_file_monitor/Classified

# 6. Accept the new state as trusted
python3 app.py --update /home/kali/project_file_monitor/Classified
```

---

## Example output

**Summary (`--check`):**

```
--------------------------------------------------------
Please find the below Details of your files being monitored:
Path being Monitored: /home/kali/project_file_monitor/Classified
Total Files Being Monitored: 33
Files Added:1
Files Deleted:1
File Content Modified:3
File Permissions Changed: 0
------------------------End-----------------------------------
```

**Detailed (`--stat`):** for each affected file, the tool prints:

```
Parent Dir : /home/kali/project_file_monitor/Classified/Agents
File Name : Agent0.txt
stat_mode : -rw-r--r--
stat_uid : 1000
stat_gid : 1000
stat_size : 818
stat_acess_time : ...
stat_modified_time : ...
stat_creation_time : ...
File Permission Change Status: False
```

**Log verification:**

```
Log-verified
There was no Log which has been altered with...
```

or, if an entry was edited:

```
There are total of 1 Log entries that are been altered with
Below Log Entry has been Altered:
...
```

---

## Log format and log verification

Each entry in `log_files/<folder>.log` looks like this:

```
{
 Message: File_path /home/kali/project_file_monitor/Classified/Agents/Agent0.txt
Status: Modified
 Date & time: 2026-11-11 02:50:49,990
 Logging_level: WARNING
}
```

Every time an entry is written, the tool computes

```
SHA-256( previous entry text + current entry text )
```

(starting from the fixed value `genesis`) and appends the result to `log_files/log_json_files/<folder>_log.json`. `--verify_log` recomputes the whole chain from the log file and compares it with the stored list:

- **An edited entry** changes its hash, so the mismatch is reported.
- **A removed or added entry** makes the two lists a different length, which is reported as well.

---

## Real-time monitoring

`--monitor <path>` uses `watchdog` (inotify) on the folder and all subfolders. It reports and logs:

| Event | Log level |
|---|---|
| File created | INFO |
| File modified | WARNING |
| File deleted | WARNING |

Repeated created/modified events for the same file within 0.5 seconds are ignored, because editors often fire several events for one save. Directory events are skipped. The folder must already have been initialised with `--init`.

---

## Running as a systemd service

Real-time monitoring only works while it is running. A service keeps it alive and restarts it after a crash.

`/etc/systemd/system/app.service`:

```ini
[Unit]
Description=File Integrity Monitor (real-time)
After=local-fs.target
# Only if the project lives in a VMware shared folder:
# RequiresMountsFor=/mnt/hgfs

[Service]
Type=simple
User=kali
WorkingDirectory=/home/kali/project_file_monitor
ExecStart=/usr/bin/python3 /home/kali/project_file_monitor/app.py --monitor /home/kali/project_file_monitor/Classified
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo install -m 644 app.service /etc/systemd/system/app.service
sudo systemctl daemon-reload
sudo systemctl enable --now app
systemctl status app
journalctl -u app -f
```

Notes:

- `WorkingDirectory` is required, because the tool reads `paths.txt` and builds its other paths from the current directory.
- Every path in `ExecStart` must be absolute.
- Use the same Python (and user) that has `watchdog` installed.

---

## Scheduled scans with cron

The service sees nothing while it is stopped. A scheduled full report closes that gap. The scheduled job runs `--stat` and appends the detailed report to `log_files/Classified_Scheduled_log.log`.

```bash
crontab -e
```

Nightly at 02:00:

```
0 2 * * * cd /home/kali/project_file_monitor && /usr/bin/python3 app.py --stat /home/kali/project_file_monitor/Classified >> /home/kali/project_file_monitor/log_files/Classified_Scheduled_log.log 2>&1
```

- `cd` first, because the tool uses relative paths.
- `>> file 2>&1` appends both normal output and errors, so failures are visible in the log.
- For testing, use `* * * * *` (every minute), then switch back and confirm with `crontab -l`.
- If the machine is **off** at the scheduled time, cron skips that run. Adding an `@reboot` entry runs a check after every boot.

---

## Exit codes

`--check` and `--stat` end with:

| Code | Meaning |
|---|---|
| `0` | No additions, deletions, content changes or permission changes |
| `1` | At least one change was found |

Always test on one line, without a pipe, because a pipe reports the last command's code instead:

```bash
python3 app.py --check /home/kali/project_file_monitor/Classified; echo $?
```

---

## Security design

| Layer | Purpose |
|---|---|
| SHA-256 file hashes | Detect any content change |
| Permission string comparison | Detect permission changes that do not alter content |
| HMAC-SHA256 signature over the baseline | Detect a baseline edited to hide changes |
| `hmac.compare_digest` | Constant-time signature comparison |
| Per-folder 32-byte random key from `secrets` | Unguessable signing key |
| Hash-chained log with a separate stored chain | Detect edited or removed log entries |
| `paths.txt` restricted to mode 600 | Keep the list of monitored paths private |
| Confirmation prompt on `--update` | Prevent accidental baseline replacement |
| systemd `Restart=on-failure` | Keep the real-time monitor running |
| Scheduled cron report | Cover periods when the monitor was not running |

---

## Known limitations

- **Signature failure is a warning, not a stop.** If the baseline signature does not match, the tool prints a warning and still uses the baseline.
- **The log chain is not keyed.** It uses plain SHA-256 and the chain is stored in a separate, unsigned file, so an attacker who edits both can rebuild a valid chain.
- **Real-time mode does not update the baseline** and does not handle rename/move events.
- **Scheduled scans (`--check`/`--stat`) print their report; they do not write added/deleted/modified entries to the chained log.** The real-time monitor does.
- **`paths.txt` is not integrity-protected, and path matching is a substring check.**
- **The protected folder must be a direct child of the project folder** (see installation).
- **VMware shared folders (`/mnt/hgfs`)** often do not deliver inotify events and may ignore `chmod`/ownership, so real-time alerts and permission checks are only reliable on the VM's own disk.
- **A stopped monitor sees nothing**, and cron skips runs while the machine is off.
- **A root attacker** can disable or rewrite everything, including the key, the code and the cron job.
- **The tool does not verify its own code files.**

---

## Attack testing

Each attack was run against the tool and the result recorded.

| # | Attack | Detected? | Notes / fix |
|---|---|---|---|
| 1 | Edit a file and fake its timestamp with `touch -d` | | |
| 2 | Edit a hash in the baseline JSON | | |
| 3 | Replace the signature file | | |
| 4 | Edit an entry in the log | | |
| 5 | Delete an entry from the log | | |
| 6 | Delete the whole log | | |
| 7 | Replace a file with a symlink | | |
| 8 | `chmod` a file only | | |
| 9 | Delete the protected folder | | |
| 10 | Stop the service, change a file, restart | | |
| 11 | Read the key as another user | | |
| 12 | Edit `paths.txt` | | |
| 13 | Edit `app.py` to skip checks | | |
| 14 | Remove the cron job | | |

---

## References

- MITRE ATT&CK: T1565 (data manipulation), T1070 (indicator removal), T1222 (file permissions modification)
- NIST SP 800-53, control SI-7 (software, firmware and information integrity)
- Comparable tools: AIDE, Tripwire
- Python: `hashlib`, `hmac`, `secrets`, `argparse`, `logging`, `pathlib`; `watchdog`

## License

For learning purposes.
