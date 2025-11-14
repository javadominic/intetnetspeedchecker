# Internet Speed Test CLI

This project provides a command-line tool to test your internet speed, including download, upload, ping, and jitter, using your hardware and service provider. The output is styled to resemble popular internet speed test CLI tools.

## Features
- Measures download and upload speeds (in Mbps)
- Reports ping and jitter (in ms)
- Shows your ISP, IP, and test server details
- Clean, user-friendly CLI output
- Estimates download / upload time for a given file size (minutes and seconds)
- Interactive prompt and non-interactive (piped) input support for the estimator

## Requirements
- Python 3.6+
- `speedtest-cli` Python package (only required for real tests; a `--simulate` mode is available for quick local checks)

## Installation
1. Clone this repository:
   ```sh
   git clone https://github.com/javadominic/intetnetspeedchecker.git
   cd intetnetspeedchecker
   ```
2. (Optional) Create and activate a virtual environment:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
Run the script from your terminal (real test requires `speedtest-cli`):

```sh
python3 internet_speed_test.py
```

The script prints ISP, server, jitter, download/upload speeds and ping.

### Transfer-time estimator (new)
After the speed scan completes the script can estimate how long it will take to download or upload a file of a given size. You can provide the size on the command line or answer interactive prompts after the test.

CLI options for the estimator:
- `--size <number>` — numeric file size to estimate (e.g. 10)
- `--unit {GB,MB,KB}` — unit for `--size` (default `GB`)
- `--direction {download,upload,both}` — which direction(s) to estimate (default `both`)
- `--simulate` — run a fast simulated test (no network or `speedtest-cli` required)

If `--size` is provided the script will print the estimate immediately. If no `--size` is given the script will prompt you after the scan. The prompt accepts piped input as well.

#### Interactive prompt (example)
```
Would you like to estimate a transfer time now? [y/N]
Direction (download/upload/both) [download]
Enter size (numeric, e.g. 1.5)
Unit (GB/MB/KB) [GB]
```

#### Piped example (answers: yes, download, 10, GB)
```sh
printf "y\ndownload\n10\nGB\n" | python3 internet_speed_test.py --simulate
```

#### Direct CLI example (no prompt)
```sh
python3 internet_speed_test.py --size 10 --unit GB --direction download
```

### Simulate mode
Use `--simulate` to run the script without installing `speedtest-cli` or using the network. The simulated results are useful to verify the CLI and estimator behavior.

```sh
python3 internet_speed_test.py --simulate
```

## How the estimator works (short)
- The script uses the measured download/upload speed (in Mbit/s), ping (ms) and jitter (ms).
- It reduces the measured throughput slightly to account for jitter relative to ping and a small protocol overhead (conservative approximation).
- It converts Mbps to bytes/sec and computes seconds = size_bytes / bytes_per_sec.
- The result is formatted as minutes and seconds for readability.

## Notes and caveats
- The estimator is approximate. It is conservative and does not model TCP slow-start, parallel streams, or server-side limits. Use it as a guide rather than an exact prediction.
- 1 GB in the estimator uses binary interpretation (1 GB = 1024^3 bytes). If you want decimal units (1e9 bytes), tell me and I can change it.
- If measured speed is 0 the estimator will report "unavailable".

## Example output (simulate)
```
Running in simulate mode (no network)
Testing from Simulated ISP (0.0.0.0)
Hosted by SimHost (SimCity, SimLand) [5 km]: 10.00 ms
Measuring jitter... Done!
Jitter:         2.00 ms
Testing download speed... Done!
Download:     100.00 Mbit/s
Testing upload speed... Done!
Upload:        20.00 Mbit/s
Ping:          10.00 ms
Estimate time to download 10.0 GB: 17m 32s

Speedtest complete.
```

## License
MIT License
