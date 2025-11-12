import sys
import time
import threading
import speedtest
import socket

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

def test_internet_speed():
    try:
        print('Retrieving speedtest.net configuration...')
        st = speedtest.Speedtest()
        st.get_servers([])
        st.get_best_server()
        server = st.best
        print(f"Testing from {st.config['client']['isp']} ({st.config['client']['ip']})")
        print(f"Hosted by {server['sponsor']} ({server['name']}, {server['country']}) [{server['d']} km]: ", end='')
        print(f"{server['latency']:.2f} ms")

        # Jitter test
        print("Measuring jitter...", end='')
        jitter = measure_jitter(server['host'].split(':')[0], int(server['host'].split(':')[1]) if ':' in server['host'] else 8080)
        print(f" Done!\nJitter:     {jitter:8.2f} ms")

        # Download test with spinner
        stop_event = threading.Event()
        t = threading.Thread(target=spinner, args=("Testing download speed", stop_event))
        t.start()
        download_speed = st.download() / 1_000_000  # Mbps
        stop_event.set()
        t.join()
        print(f"Download:   {download_speed:8.2f} Mbit/s")

        # Upload test with spinner
        stop_event = threading.Event()
        t = threading.Thread(target=spinner, args=("Testing upload speed", stop_event))
        t.start()
        upload_speed = st.upload() / 1_000_000  # Mbps
        stop_event.set()
        t.join()
        print(f"Upload:     {upload_speed:8.2f} Mbit/s")

        print(f"Ping:       {st.results.ping:8.2f} ms")
        print("\nSpeedtest complete.")
    except Exception as e:
        print(f"Error during speed test: {e}")

if __name__ == "__main__":
    test_internet_speed()
