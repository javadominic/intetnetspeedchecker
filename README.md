# Internet Speed Test CLI

This project provides a command-line tool to test your internet speed, including download, upload, ping, and jitter, using your hardware and service provider. The output is styled to resemble popular internet speed test CLI tools.

## Features
- Measures download and upload speeds (in Mbps)
- Reports ping and jitter (in ms)
- Shows your ISP, IP, and test server details
- Clean, user-friendly CLI output

## Requirements
- Python 3.6+
- `speedtest-cli` Python package

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
Run the script from your terminal:
```sh
python internet_speed_test.py
```

You will see output similar to:
```
Retrieving speedtest.net configuration...
Testing from YourISP (YourIP)
Hosted by ServerName (City, Country) [Distance km]: XX.XX ms
Measuring jitter... Done!
Jitter:      XX.XX ms
Testing download speed... Done!
Download:    XX.XX Mbit/s
Testing upload speed... Done!
Upload:      XX.XX Mbit/s
Ping:        XX.XX ms

Speedtest complete.
```

## Notes
- The script uses the `speedtest-cli` library to perform tests.
- Jitter is calculated as the mean absolute difference between consecutive TCP connection pings to the test server.
- The `.gitignore` is set up to exclude IDE, environment, and build files.

## License
MIT License
