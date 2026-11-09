#!/usr/bin/env python3

import requests
import threading
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
import re
from colorama import Fore, Style, init

init(autoreset=True)


def animated_logo():
    logo = [
        "██████╗░███████╗██╗░░░██╗░█████╗░",
        "██╔══██╗██╔════╝██║░░░██║██╔══██╗",
        "██████╔╝█████╗░░╚██╗░██╔╝██║░░██║",
        "██╔══██╗██╔══╝░░░╚████╔╝░██║░░██║",
        "██║░░██║███████╗░░╚██╔╝░░╚█████╔╝",
        "╚═╝░░╚═╝╚══════╝░░░╚═╝░░░░╚════╝░"
    ]


    glow_colors = [
        '\033[38;5;109m', '\033[38;5;110m', '\033[38;5;116m',
        '\033[38;5;151m', '\033[38;5;152m', '\033[38;5;146m',
        '\033[38;5;183m', '\033[38;5;182m',
    ]
    rainbow_colors = [
        '\033[38;2;130;170;190m', '\033[38;2;145;185;175m',
        '\033[38;2;190;195;145m', '\033[38;2;155;190;160m',
        '\033[38;2;145;165;195m', '\033[38;2;175;155;190m',
        '\033[38;2;195;160;175m',
    ]
    print('\033[2J\033[H\033[?25l', end='')
    try:
       for frame in range(20):
            print('\033[H', end='')
            title_color = glow_colors[frame % len(glow_colors)]
            print(f"\n")
            for i, line in enumerate(logo):
                colored_line = ""
                for j, char in enumerate(line):
                    if char not in ('⠀', ' '):
                        idx = (frame + i + j) % len(rainbow_colors)
                        colored_line += rainbow_colors[idx] + char + '\033[0m'
                    else:
                        colored_line += char
                print(f"    {colored_line}")

            bc = glow_colors[(frame + 3) % len(glow_colors)]
            print(f"{bc}      github.com/mdleet")
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print('\033[?25h', end='')


class ReverseIPLookup:
    def __init__(self):
        self.results = {}
        self.lock = threading.Lock()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                           '(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36'),
            'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                       'image/jxl,image/avif,image/webp,image/apng,*/*;q=0.8'),
            'Accept-Language': 'en-GB,en;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cookie': 'international=2',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-GPC': '1',
        })
        self.success_count = 0
        self.failed_count = 0
        self.total_domains = 0

    def create_result_dir(self):
        if not os.path.exists('Result'):
            os.makedirs('Result')

    def save_results(self, ip, domains):
        try:
            with open('Result/ip_domains.txt', 'a', encoding='utf-8') as f:
                f.write(f"{ip}: {', '.join(domains)}\n")
                f.flush()

            with open('Result/d.txt', 'a', encoding='utf-8') as f:
                for d in domains:
                    f.write(f"{d}\n")
                f.flush()
        except Exception:
            pass

    def extract_domains(self, html_content):
        domains = set()

        list_block = ""
        m = re.search(r'<ul\s+id="list"[^>]*>(.*?)</ul>', html_content,
                      re.DOTALL | re.IGNORECASE)
        if m:
            list_block = m.group(1)
        else:
            m = re.search(r'<div class="result result2"[^>]*>(.*?)</div>\s*<div',
                          html_content, re.DOTALL | re.IGNORECASE)
            list_block = m.group(1) if m else html_content

        pattern = r'<a\s+href="/([^"/]+)/"[^>]*>\s*([^<]+?)\s*</a>'
        for href_part, text in re.findall(pattern, list_block, re.IGNORECASE):
            domain = text.strip().lower()

            if not domain or '.' not in domain:
                continue
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', domain):
                continue
            if domain in ('绑定过的域名如下：', '上的网站'):
                continue
            if not re.match(r'^[a-z0-9][a-z0-9\-\.]*\.[a-z]{2,}$', domain):
                continue

            domains.add(domain)

        return sorted(domains)

    def lookup_ip(self, ip):
        ip = ip.strip()
        if not ip:
            return

        if not re.match(r'^\d{1,3}(\.\d{1,3}){3}$', ip):
            with self.lock:
                self.failed_count += 1
                print(f"{Fore.RED}[-] {ip:<20}    =>  Invalid IP{Style.RESET_ALL}")
            return

        try:
            url = f"https://site.ip138.com/{quote(ip)}/"
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()

            domains = self.extract_domains(response.text)

            with self.lock:
                if domains:
                    self.results[ip] = domains
                    self.success_count += 1
                    self.total_domains += len(domains)
                    print(f"{Fore.GREEN}[+] {ip:<20}    =>  {len(domains)} domains{Style.RESET_ALL}")
                    for d in domains:
                        print(f"    {Fore.CYAN}└── {d}{Style.RESET_ALL}")
                    self.save_results(ip, domains)
                else:
                    self.results[ip] = []
                    self.failed_count += 1
                    print(f"{Fore.RED}[-] {ip:<20}    =>  No domains{Style.RESET_ALL}")

        except requests.exceptions.Timeout:
            with self.lock:
                self.failed_count += 1
                print(f"{Fore.RED}[-] {ip:<20}    =>  Timeout{Style.RESET_ALL}")
        except requests.exceptions.RequestException:
            with self.lock:
                self.failed_count += 1
                print(f"{Fore.RED}[-] {ip:<20}    =>  Failed{Style.RESET_ALL}")
        except Exception:
            with self.lock:
                self.failed_count += 1
                print(f"{Fore.RED}[-] {ip:<20}    =>  Failed{Style.RESET_ALL}")

    def load_ips(self, filename):
        try:
            if not os.path.exists(filename):
                print(f"{Fore.RED}File {filename} not found!{Style.RESET_ALL}")
                return []
            with open(filename, 'r', encoding='utf-8') as f:
                ips = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            return ips
        except Exception as e:
            print(f"{Fore.RED}Error loading IPs: {e}{Style.RESET_ALL}")
            return []

    def run(self):
        animated_logo()

        try:
            print(f"\n")
            ip_file = input(f"{Fore.YELLOW}Enter Your IPList file: {Style.RESET_ALL}").strip()
            if not ip_file:
                ip_file = "ips.txt"

            threads_input = input(f"{Fore.YELLOW}Enter Your Threads (max 100): {Style.RESET_ALL}").strip()
            try:
                max_threads = int(threads_input) if threads_input else 20
                max_threads = max(1, min(max_threads, 100))
            except ValueError:
                max_threads = 20
        except KeyboardInterrupt:
            print(f"\n{Fore.MAGENTA}Goodbye!{Style.RESET_ALL}")
            return

        ips = self.load_ips(ip_file)
        if not ips:
            return

        self.create_result_dir()
        for fname in ('Result/ip_domains.txt', 'Result/d.txt'):
            with open(fname, 'w', encoding='utf-8') as f:
                f.write('')

        print(f"\n{Fore.GREEN}Starting with {max_threads} threads on {len(ips)} IPs...{Style.RESET_ALL}\n")
        print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(self.lookup_ip, ip) for ip in ips]
            for _ in as_completed(futures):
                pass

        print(f"\n{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}Completed!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}   Success: {self.success_count} IPs{Style.RESET_ALL}")
        print(f"{Fore.RED}   Failed : {self.failed_count} IPs{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   Total domains found: {self.total_domains}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Results saved to:{Style.RESET_ALL}")
        print(f"   - Result/ip_domains.txt  (IP: domain1, domain2, ...)")
        print(f"   - Result/d.txt           (domains only)")


if __name__ == "__main__":
    try:
        scanner = ReverseIPLookup()
        scanner.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Interrupted by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
