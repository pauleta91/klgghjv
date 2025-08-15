#!/usr/bin/env python3
import time
import argparse
import subprocess

def run_cmd(cmd):
    """Run EOS CLI command and return output."""
    try:
        return subprocess.check_output(['Cli', '-c', cmd], text=True)
    except subprocess.CalledProcessError as e:
        print(f"cmd failed: {e}")
        return ""
    except FileNotFoundError:
        print("Cli not found. Make sure you are on an Arista EOS switch.")
        raise

def no_shut(interface):
    print(f"no-shut {interface}")
    run_cmd("configure terminal")
    run_cmd(f"interface {interface}")
    run_cmd("no shutdown")

def shut(interface):
    print(f"shut {interface}")
    run_cmd("configure terminal")
    run_cmd(f"interface {interface}")
    run_cmd("shutdown")

def bounce(interface):
    """Shut and no-shut the interface."""
    shut(interface)
    no_shut(interface)

def ping(ip, vrf):
    """Ping IP once in the given VRF."""
    cmd = f"ping {ip} vrf {vrf} repeat 1 timeout 1"
    try:
        output = run_cmd(cmd)
        return "Success rate is 100 percent" in output
    except Exception as e:
        print(f"ping failed: {e}")
        return False

def int_up(interface, timeout=60):
    """Wait until interface is connected, polling every 1 sec up to timeout seconds."""
    start = time.time()
    while time.time() - start < timeout:
        out = run_cmd(f"show interfaces {interface} status")
        for line in out.splitlines():
            if line.startswith(interface) and len(line.split()) > 2:
                if line.split()[2].lower() == "connected":
                    return True
        time.sleep(1)
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
            print(f"\n== cycle {cycle} ==")
            bounce(args.interface)

            if not int_up(args.interface):
                print("Interface did not come up. Exiting.")
                break

            for i in range(3):
                if ping(args.ip_address, args.vrf):
                    print("Ping succeeded")
                    break
                print("Ping failed. Retrying...")
                time.sleep(2)
            else:
                print("Ping failed 3 times. Exiting.")
                break

    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        if not int_up(args.interface, 2):
            no_shut(args.interface)
        print("Done")

if __name__ == "__main__":
    main()
