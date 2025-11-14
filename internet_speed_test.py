import sys
import time
import threading
import socket
import argparse

# safe import: speedtest-cli provides the `speedtest` module; if it's not installed
# we keep `speedtest` as None and allow --simulate to run without it.
try:
    import speedtest
except Exception:
    speedtest = None


def spinner(label, stop_event):
    spinner_chars = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f'\r{label} {spinner_chars[idx % len(spinner_chars)]}')
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write(f'\r{label}... Done!\n')
    sys.stdout.flush()


def measure_jitter(host, port=8080, count=10, timeout=2):
    pings = []
    for _ in range(count):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            start = time.time()
            s.connect((host, port))
            end = time.time()
            s.close()
            pings.append((end - start) * 1000)  # ms
        except Exception:
            pings.append(timeout * 1000)
        time.sleep(0.1)
    if len(pings) < 2:
        return 0.0
    diffs = [abs(pings[i] - pings[i-1]) for i in range(1, len(pings))]
    return sum(diffs) / len(diffs)


def bytes_from_unit(size: float, unit: str) -> float:
    unit = (unit or "").lower()
    if unit in ("gb", "g"):
        return size * (1024 ** 3)
    if unit in ("mb", "m"):
        return size * (1024 ** 2)
    if unit in ("kb", "k"):
        return size * 1024
    return size


def human_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    if seconds < 1:
        return f"{seconds*1000:.0f} ms"
    mins, sec = divmod(int(round(seconds)), 60)
    hours, mins = divmod(mins, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if mins:
        parts.append(f"{mins}m")
    parts.append(f"{sec}s")
    return " ".join(parts)


def estimate_time_seconds(size_bytes: float, speed_mbps: float, ping_ms: float, jitter_ms: float) -> float:
    """Estimate transfer time (seconds) for size_bytes using measured speed (Mbps).

    A conservative reduction factor is applied to account for jitter/protocol overhead.
    """
    if speed_mbps <= 0:
        return float("inf")
    # Adjust for jitter relative to latency, capped at 50% reduction
    jitter_ratio = 0.0
    if ping_ms + jitter_ms > 0:
        jitter_ratio = min(jitter_ms / (ping_ms + jitter_ms + 1e-6), 0.5)
    overhead = 0.98
    effective_mbps = speed_mbps * (1.0 - jitter_ratio) * overhead
    # convert Mbps to bytes/sec (1 Mbps = 1_000_000 bits/sec)
    bytes_per_sec = effective_mbps * 1_000_000.0 / 8.0
    return size_bytes / bytes_per_sec


def test_internet_speed(size=None, unit='GB', direction='both', simulate=False, preanswers=None):
    try:
        # initialize variables so all code paths have them defined
        download_speed = 0.0
        upload_speed = 0.0
        ping_val = 0.0
        jitter = 0.0
        server = {'host': ''}

        if simulate:
            # simulated values for quick local testing
            print('Running in simulate mode (no network)')
            isp = 'Simulated ISP'
            server = {'sponsor': 'SimHost', 'name': 'SimCity', 'country': 'SimLand', 'd': 5, 'host': ''}
            download_speed = 100.0
            upload_speed = 20.0
            ping_val = 10.0
            jitter = 2.0
            print(f"Testing from {isp} (0.0.0.0)")
            print(f"Hosted by {server['sponsor']} ({server['name']}, {server['country']}) [{server['d']} km]: ", end='')
            print(f"{ping_val:.2f} ms")
        else:
            print('Retrieving speedtest.net configuration...')
            if speedtest is None:
                print("The 'speedtest' package is not installed. Install with: pip install speedtest-cli")
                return
            st = speedtest.Speedtest()
            st.get_servers([])
            st.get_best_server()
            server = st.best
            print(f"Testing from {st.config['client']['isp']} ({st.config['client']['ip']})")
            print(f"Hosted by {server['sponsor']} ({server['name']}, {server['country']}) [{server['d']} km]: ", end='')
            print(f"{server['latency']:.2f} ms")

        # Jitter test (only attempt to measure when we have a real server host)
        print("Measuring jitter...", end='')
        if not simulate and server.get('host'):
            host_only = server['host'].split(':')[0]
            port = int(server['host'].split(':')[1]) if ':' in server['host'] else 80
            jitter = measure_jitter(host_only, port)
        # for simulated or missing-host cases, jitter value already set
        print(f" Done!\nJitter:     {jitter:8.2f} ms")

        # Download test with spinner
        stop_event = threading.Event()
        t = threading.Thread(target=spinner, args=("Testing download speed", stop_event))
        t.start()
        if not simulate:
            download_speed = st.download() / 1_000_000  # Mbps
        else:
            # small pause to show spinner briefly
            time.sleep(0.3)
            download_speed = download_speed
        stop_event.set()
        t.join()
        print(f"Download:   {download_speed:8.2f} Mbit/s")

        # Upload test with spinner
        stop_event = threading.Event()
        t = threading.Thread(target=spinner, args=("Testing upload speed", stop_event))
        t.start()
        if not simulate:
            upload_speed = st.upload() / 1_000_000  # Mbps
        else:
            time.sleep(0.3)
            upload_speed = upload_speed
        stop_event.set()
        t.join()
        print(f"Upload:     {upload_speed:8.2f} Mbit/s")

        if simulate:
            ping_display = ping_val
        else:
            # st.results.ping may be present from speedtest module
            ping_display = getattr(st.results, 'ping', None) if not simulate and 'st' in locals() else None
            if ping_display is None:
                ping_display = 0.0
        print(f"Ping:       {ping_display:8.2f} ms")
        # If user requested an estimate for a given file size, calculate it now
        if size is not None and size > 0:
            total_bytes = bytes_from_unit(size, unit)
            ping_ms = ping_display or 0.0
            jitter_ms = jitter or 0.0
            if direction in ('download', 'both'):
                sec = estimate_time_seconds(total_bytes, download_speed, ping_ms, jitter_ms)
                print(f"Estimate time to download {size} {unit}: {human_time(sec)}")
            if direction in ('upload', 'both'):
                sec = estimate_time_seconds(total_bytes, upload_speed, ping_ms, jitter_ms)
                print(f"Estimate time to upload   {size} {unit}: {human_time(sec)}")
        else:
            # If no size provided: attempt to ask the user. We try reading input() so
            # this works for interactive TTYs and for piped answers. Treat EOF as
            # "no".
            try:
                # helper to read either from preanswers (piped stdin) or interactively
                answers_iter = iter(preanswers) if preanswers else None

                def get_answer(prompt, default=None):
                    if answers_iter is not None:
                        try:
                            a = next(answers_iter)
                            # emulate input() trimming
                            return a.strip()
                        except StopIteration:
                            return default
                    try:
                        return input(prompt)
                    except EOFError:
                        return default

                want = (get_answer('\nWould you like to estimate a transfer time now? [y/N]: ', 'n') or 'n').strip().lower()
            except EOFError:
                want = 'n'
            except Exception:
                want = 'n'
            if want in ('y', 'yes'):
                # ask direction
                while True:
                    try:
                        d = (get_answer('Direction (download/upload/both) [download]: ', 'download') or 'download').strip().lower()
                    except EOFError:
                        d = 'download'
                    if d in ('download', 'upload', 'both'):
                        break
                    print("Please enter 'download', 'upload', or 'both'.")
                # ask size
                while True:
                    try:
                        s = (get_answer('Enter size (numeric, e.g. 1.5): ', '') or '').strip()
                    except EOFError:
                        s = ''
                    try:
                        size_val = float(s)
                        if size_val <= 0:
                            print('Enter a positive number.')
                            continue
                        break
                    except Exception:
                        print('Invalid number, try again.')
                # unit
                u = (get_answer('Unit (GB/MB/KB) [GB]: ', 'GB') or 'GB').strip().upper()
                if u not in ('GB', 'MB', 'KB'):
                    u = 'GB'
                total_bytes = bytes_from_unit(size_val, u)
                ping_ms = ping_display or 0.0
                jitter_ms = jitter or 0.0

                def format_min_sec(seconds: float) -> str:
                    if seconds == float('inf'):
                        return 'unavailable'
                    s = int(round(seconds))
                    mins = s // 60
                    secs = s % 60
                    if mins > 0:
                        return f"{mins}m {secs}s"
                    return f"{secs}s"

                if d in ('download', 'both'):
                    sec = estimate_time_seconds(total_bytes, download_speed, ping_ms, jitter_ms)
                    print(f"Estimate time to download {size_val} {u}: {format_min_sec(sec)}")
                if d in ('upload', 'both'):
                    sec = estimate_time_seconds(total_bytes, upload_speed, ping_ms, jitter_ms)
                    print(f"Estimate time to upload   {size_val} {u}: {format_min_sec(sec)}")
        print("\nSpeedtest complete.")
    except Exception as e:
        print(f"Error during speed test: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run internet speed test and optionally estimate transfer time')
    parser.add_argument('--simulate', action='store_true', help='Run a simulated test (no network)')
    parser.add_argument('--size', type=float, help='File size to estimate (numeric)')
    parser.add_argument('--unit', choices=['GB', 'MB', 'KB'], default='GB', help='Unit for --size')
    parser.add_argument('--direction', choices=['download', 'upload', 'both'], default='both', help='Estimate direction')
    args = parser.parse_args()
    # If stdin is not a TTY, read remaining lines to use as pre-answers for prompts
    preanswers = None
    try:
        if not sys.stdin.isatty():
            data = sys.stdin.read()
            if data:
                preanswers = data.splitlines()
    except Exception:
        preanswers = None

    test_internet_speed(size=args.size, unit=args.unit, direction=args.direction, simulate=args.simulate, preanswers=preanswers)
