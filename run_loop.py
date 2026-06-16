"""
run_loop.py — Varsany Automation Daemon
Runs continuously. Every 3 seconds it checks the live database
for unprocessed orders and generates PSD files automatically.

Usage:
    py run_loop.py              # normal production run
    py run_loop.py --dry-run    # preview only, no files written
    py run_loop.py --interval 5  # override poll interval
"""

import sys, os, time, argparse, traceback
from datetime import datetime

# ── Import the batch processor ────────────────────────────────────────────────
# run_loop.py must be in the same folder as batch_processor.py
sys.path.insert(0, os.path.dirname(__file__))
from batch_processor import run_batch, log
# Note: batch_processor loads .env via load_dotenv(), so NAS_PASS is available here.

POLL_SECONDS = 3  # default poll interval

# NAS upload is enabled automatically when NAS_PASS is set in .env
_nas_default = bool(os.environ.get("NAS_PASS"))


def main():
    parser = argparse.ArgumentParser(description="Varsany Automation Daemon")
    parser.add_argument("--dry-run",    action="store_true", help="Preview only — no files written")
    parser.add_argument("--interval",   type=int, default=POLL_SECONDS, help="Seconds between polls (default 3)")
    parser.add_argument("--nas",    dest="upload_nas", action="store_true",  default=_nas_default,
                        help="Upload finished PSDs to Synology NAS (auto-enabled when NAS_PASS is set in .env)")
    parser.add_argument("--no-nas", dest="upload_nas", action="store_false",
                        help="Disable Synology NAS upload even if credentials are configured")
    parser.add_argument("--hours",       type=int, default=None,
                        help="Only process orders added in the last N hours (recommended: 24)")
    parser.add_argument("--date-after",  type=str, default=None,
                        help="Only process orders placed on or after this date e.g. 2026-05-21")
    args = parser.parse_args()

    interval = args.interval

    # Capture startup time — only orders placed AFTER this moment are processed.
    # Overridden by --date-after if explicitly passed.
    startup_cutoff = args.date_after or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    log("=" * 60)
    log(f"Varsany Automation Daemon started  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Poll interval : {interval}s")
    log(f"Processing orders after : {startup_cutoff}")
    log(f"Dry run       : {args.dry_run}")
    log(f"NAS upload    : {args.upload_nas}  (host: {os.environ.get('NAS_HOST', 'not set')})")
    log("Press Ctrl+C to stop")
    log("=" * 60)

    while True:
        try:
            run_batch(
                dry_run      = args.dry_run,
                upload_nas   = args.upload_nas,
                hours        = args.hours,
                date_after   = startup_cutoff,
            )
        except KeyboardInterrupt:
            log("Daemon stopped by user.")
            break
        except Exception as e:
            log(f"Unexpected error: {e}", "ERROR")
            log(traceback.format_exc()[-600:], "ERROR")

        log(f"Sleeping {interval}s until next poll...")
        time.sleep(interval)


if __name__ == "__main__":
    main()
