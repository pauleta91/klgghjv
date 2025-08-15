#!/usr/bin/env python3
import time
import sys
from cli import cli  # EOS Python module to run CLI commands

def get_user_input():
    interface = input("Enter interface: ").strip()
    ip = input("Enter IP address to ping: ").strip()
    vrf = input("Enter VRF (default if none): ").strip() or "default"
    return interface, ip, vrf

def flap_interface(interface):
    """Shut and no shut the interface."""
    cli(f"enable")
    cli(f"configure terminal")
    cli(f"interface {interface}")
    cli(f"shutdown")
    cli(f"no shutdown")

def wait_until_connected(interface):
    """Poll every second until interface is connected."""
    while True:
        output = cli(f"show interfaces {interface} | include line protocol|is up")
        # Check for "line protocol is up" indicating connected
        if "line protocol is up" in output:
            return
        time.sleep(1)

def ping_ip(ip, vrf):
    """Ping the IP in the given VRF once."""
    cmd = f"ping {ip} vrf {vrf} repeat 1 timeout 1"
    output = cli(cmd)
    # Success if 'Success rate is 100 percent' appears in output
    if "Success rate is 100 percent" in output:
        return True
    return False

def main():
    interface, ip, vrf = get_user_input()
    
    while True:
        success = False
        for attempt in range(1, 4):  # Up to 3 attempts
            print(f"\nFlap attempt {attempt}...")
            flap_interface(interface)
            print("Waiting for interface to become connected...")
            wait_until_connected(interface)
            print(f"Pinging {ip} in VRF {vrf}...")
            if ping_ip(ip, vrf):
                print("Ping successful! Repeating process...\n")
                success = True
                break  # Success, go back to start of while loop
            else:
                print(f"Ping failed on attempt {attempt}. Retrying...")
        
        if not success:
            print("Ping failed after 3 attempts. Exiting script.")
            sys.exit(1)

if __name__ == "__main__":
    main()
