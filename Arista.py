import time
import argparse
import json
from Cli import cli

def run_cmd(cmd):
    try:
        return cli(cmd)
    except Exception as e:
        print(f"cmd failed: {e}")
        return ""

def no_shut(interface):
    print(f"no-shut {interface}")
    run_cmd(f"configure terminal")
    run_cmd(f"interface {interface}")
    run_cmd("no shutdown")

def shut(interface):
    print(f"shut {interface}")
    run_cmd(f"configure terminal")
    run_cmd(f"interface {interface}")
    run_cmd("shutdown")

def bounce(interface):
    shut(interface)
    no_shut(interface)

def ping(ip, vrf):
    try:
        if vrf.lower() != "default":
            out = run_cmd(f"ping vrf {vrf} {ip} count 1")
        else:
            out = run_cmd(f"ping {ip} count 1")
        return "1 packets received" in out or "1 received" in out
    except Exception as e:
        print(f"ping blew up: {e}")
        return False

def int_up(interface, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            out = run_cmd(f"show interfaces {interface} status | json")
            data = json.loads(out)
            if data.get('interfaceStatuses', {}).get(interface, {}).get('lineProtocolStatus') == "up":
                return True
        except Exception as e:
            print(f"status check failed: {e}")
        time.sleep(1)
    return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("interface")
    p.add_argument("ip_address")
    p.add_argument("vrf")
    args = p.parse_args()

    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"== cycle {cycle} ==")
            bounce(args.interface)

            if not int_up(args.interface):
                print("int stayed dead. quitting.")
                break

            for i in range(3):
                if ping(args.ip_address, args.vrf):
                    print("ping works")
                    break
                print("ping failed. retrying...")
                time.sleep(2)
            else:
                print("ping hopeless after 3 tries. quitting.")
                break

    except KeyboardInterrupt:
        print("killed")
    finally:
        if not int_up(args.interface, 2):
            no_shut(args.interface)
        print("done")

if __name__ == "__main__":
    main()
