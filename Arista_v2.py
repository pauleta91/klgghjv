#!/usr/bin/env python3
import time
import sys
import argparse
import subprocess

def run_cli(command):
    """Run a single EOS CLI command and return stdout."""
    result = subprocess.run(["Cli", "-c", command], capture_output=True, text=True)
    return result.stdout

def shut(interface):
    """Shut the interface using separate Cli calls."""
    run_cli(f"interface {interface}")
    run_cli("shutdown")

def no_shut(interface):
    """No shutdown the interface using separate Cli calls."""
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

def ping(ip):
    """Ping IP once from management1 using the current VRF."""
    # No VRF argument needed; assumed VRF already set
    output = run_cli(f'ping {ip} count 1 source management1')
    
    print("----- Ping Output Start -----")
    print(output)
    print("------ Ping Output End ------")
    
    # Simple check: if any packets received, success
    if "1 received" in output:
        return True
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("interface", help="Interface to flap")
    parser.add_argument("ip_address", help="IP address to ping")
    parser.add_argument("vrf", help="VRF to use for ping")
    args = parser.parse_args()

    # Set VRF once at the start
    print(f"Setting CLI VRF context to {args.vrf}...")
    run_cli(f"cli vrf {args.vrf}")

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

                print(f"Pinging {args.ip_address} from management1...")
                if ping(args.ip_address):
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
