import time
import sys
import subprocess

def run_cli(command):
    """Run an EOS CLI command using subprocess and return output as string."""
    result = subprocess.run(["Cli", "-c", command], capture_output=True, text=True)
    return result.stdout

def get_user_input():
    interface = input("Enter interface (e.g., Ethernet1): ").strip()
    ip = input("Enter IP address to ping: ").strip()
    vrf = input("Enter VRF (default if none): ").strip() or "default"
    return interface, ip, vrf

def flap_interface(interface):
    """Shut and no shut the interface."""
    run_cli(f"enable")
    run_cli(f"configure terminal")
    run_cli(f"interface {interface}")
    run_cli(f"shutdown")
    run_cli(f"no shutdown")

def wait_until_connected(interface):
    """Poll every second until interface is connected."""
    while True:
        output = run_cli(f"show interfaces {interface} | include line protocol|is up")
        if "line protocol is up" in output:
            return
        time.sleep(1)

def ping_ip(ip, vrf):
    """Ping the IP in the given VRF once."""
    output = run_cli(f"ping {ip} vrf {vrf} repeat 1 timeout 1")
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
