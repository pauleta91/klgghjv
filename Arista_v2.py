#!/usr/bin/env python3
import time
import sys
import argparse
import subprocess

def run_cli(command):
    payload = (command.replace(";", r"\n"))
    cmd = f"Cli -p15 -c $'{payload}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def shut(interface):
    run_cli(f"conf;interface {interface};shutdown")

def no_shut(interface):
    run_cli(f"conf;interface {interface};no shutdown")

def bounce(interface):
    shut(interface)
    no_shut(interface)

def int_up(interface, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        output = run_cli(f"show interfaces {interface} | include connected")
        if "connected" in output:
            return True
        time.sleep(1)
    return False
def ping(ip, vrf):
    output = run_cli(f'ping {ip} vrf {vrf} count 2 source management1')
    if "0 received" in output:
        return False 
    return True

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

                print(f"Pinging {args.ip_address} in VRF {args.vrf} from management1...")
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
