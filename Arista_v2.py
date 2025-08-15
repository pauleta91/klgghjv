#!/usr/bin/env python3
import time
import sys
import argparse
import subprocess
import re

def run_cli(command):
    """Run a single EOS CLI command and return stdout."""
    result = subprocess.run(["Cli", "-c", command], capture_output=True, text=True)
    return result.stdout

def shut(interface):
    """Shut the interface."""
    run_cli("enable")
    run_cli("configure terminal")
    run_cli(f"interface {interface}")
    run_cli("shutdown")

def no_shut(interface):
    """No shutdown the interface."""
    run_cli("enable")
    run_cli("configure terminal")
    run_cli(f"interface {interface}")
    run_cli("no shutdown")

def bounce(interface):
    """Shut and no-shut the interface."""
    shut(interface)
    no_shut(interface)

def int_up(interface):
    """Wait until interface shows 'line protocol is up'."""
    while True:
        output = run_cli(f"show interfaces {interface} | include line protocol|is up")
        if "line protocol is up" in output:
            return True
        time.sleep(1)

def ping(ip, vrf, source="Management1"):
    """Ping IP once in the specified VRF from Management1.
       Returns True if at least one packet is received."""
    output = run_cli(f"ping {ip} vrf {vrf} count 1 source {source}")
    # Use regex to reliably parse transmitted and received packets
    match = re.search(r"(\d+)\s+packets transmitted,\s+(\d+)\s+received", output)
    if match:
        transmitted = int(match.group(1))
        received = int(match.group(2))
        return received > 0
    else:
        print("Ping output not recognized, marking as failure.")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("interface", help="Interface to flap")
    parser.add_argument("ip_address", help="IP address to ping")
    parser.add_argument("vrf", help="VRF to use for ping")
    args = parser.parse_args()

    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"\n== Cycle {cycle} ==")
            success = False

            for attempt in range(1, 4):
                print(f"Flap attempt {attempt}...")
                bounce(args.interface)

                print("Waiting for interface to become connected...")
                int_up(args.interface)

                print(f"Pinging {args.ip_address} in VRF {args.vrf} from Management1...")
                if ping(args.ip_address, args.vrf):
                    print("Ping successful! Repeating process...\n")
                    success = True
                    break
                else:
                    print(f"Ping failed on attempt {attempt}. Retrying...")

            if not success:
                print("Ping failed after 3 attempts. Exiting script.")
                sys.exit(1)

    except KeyboardInterrupt:
        print("Script interrupted by user. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()
