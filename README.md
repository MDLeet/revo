# REVO Reverse IP Lookup Tool

A Python script that performs reverse IP lookup to find domains associated with an IP address.

## Features
- Reads IPs from a text file
- Multi-threaded (max 100, recommended 10–20)
- Colored terminal output with animated banner
- Saves results to `Result/ip_domains.txt` and `Result/d.txt`
- Handles timeouts, invalid IPs, and empty results

## Requirements
- Python 3.7+
- `pip install requests colorama`

## Usage
1. Create `ips.txt` with one IP per line:
