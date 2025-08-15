import time
import argparse
import subprocess
import sys

def execute_command(command):
    """
    Executes a CLI command on the Nexus switch by calling the 'vsh' executable
    directly as a subprocess.
    """
    print(f"Executing: {command}")
    try:
        return subprocess.check_output(['vsh', '-c', command]).decode('utf-8')
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error executing command with 'vsh': {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def no_shut_interface(interface):
    """Ensures the interface is in a 'no shutdown' state."""
    print(f"Ensuring interface {interface} is enabled...")
    try:
        execute_command(f"conf t ; interface {interface} ; no shutdown")
        print(f"Interface {interface} is set to 'no shutdown'.")
    except Exception as e:
        print(f"Failed to enable interface {interface}: {e}")

def bounce_interface(interface):
    """
    Performs a shutdown and no shutdown on the specified interface, with a delay
    to allow the interface to initialize.
    """
    print(f"--- Bouncing interface {interface} ---")
    execute_command(f"conf t ; interface {interface} ; shutdown")
    print(f"Interface {interface} is shut down.")
    no_shut_interface(interface)
    print(f"Waiting 3 seconds for initialization...")
    time.sleep(3)

def check_ping(ip_address, vrf, count=1):
    """
    Sends a number of pings to the specified IP in the given VRF.
    Returns True if the ping command's exit code is 0, False otherwise.
    """
    print(f"--- Pinging {ip_address} in VRF {vrf} ---")
    command = f"ping {ip_address} vrf {vrf} count {count}"
    try:
        process = subprocess.run(['vsh', '-c', command], 
                                 capture_output=True, 
                                 text=True, 
                                 timeout=15)
        return process.returncode == 0
    except Exception as e:
        print(f"An unexpected error occurred during ping execution: {e}")
        return False

def verify_interface_status(interface, timeout=60):
    """
    Verifies that the interface is in an 'up' or 'connected' state.
    """
    print(f"--- Verifying status for interface {interface} ---")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output = execute_command(f"show interface {interface} status")
            for line in output.strip().split('\n'):
                if line.strip().startswith(interface):
                    parts = line.split()
                    if len(parts) > 2:
                        status = parts[2].lower()
                        print(f"Parsed status: '{status}'")
                        if status in ["up", "connected"]:
                            print(f"SUCCESS: Interface {interface} is confirmed to be {status}.")
                            return True
        except Exception as e:
            print(f"Could not verify interface status: {e}")
        
        print("Interface state not yet 'up' or 'connected'. Waiting...")
        time.sleep(5)
    
    print(f"ERROR: Interface {interface} did not come up within {timeout} seconds.")
    return False

def main():
    """Main function to execute the script logic."""
    parser = argparse.ArgumentParser(
        description="A Python script for Cisco Nexus 9000 to continuously bounce an interface and test connectivity."
    )
    parser.add_argument("interface", help="The interface to manage (e.g., Ethernet1/1).")
    parser.add_argument("ip_address", help="The IP address to ping.")
    parser.add_argument("vrf", help="The VRF name to use for the ping.")
    
    args = parser.parse_args()
    cycle_count = 0

    try:
        while True:
            cycle_count += 1
            print(f"\n{'='*20} CYCLE {cycle_count} {'='*20}")

            # 1. Bounce the interface
            bounce_interface(args.interface)

            # 2. Wait for it to come up
            if not verify_interface_status(args.interface):
                print("Interface failed to come up. Exiting script.")
                break

            # 3. Attempt to ping up to 3 times
            ping_successful = False
            for attempt in range(1, 4):
                print(f"--- Ping Attempt {attempt} of 3 ---")
                if check_ping(args.ip_address, args.vrf):
                    print(f"SUCCESS: Ping to {args.ip_address} was successful.")
                    ping_successful = True
                    break
                else:
                    print(f"Ping failed. Waiting 5 seconds before retry...")
                    time.sleep(5)
            
            # 4. Check the final ping result
            if not ping_successful:
                print(f"\nFAILURE: Ping to {args.ip_address} was not successful after 3 attempts.")
                print("--- Exiting script ---")
                break # Exit the main while loop
            else:
                print(f"--- Cycle {cycle_count} successful. Starting next cycle. ---")

    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    finally:
        print("Ensuring interface is left in an enabled state before exiting.")
        no_shut_interface(args.interface)
        print("Script finished.")

if __name__ == "__main__":
    main()
