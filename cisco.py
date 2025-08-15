import time
import argparse
import subprocess

def execute_command(command):
    """
    Executes a CLI command on the Nexus switch by calling the 'vsh' executable
    directly as a subprocess.
    """
    print(f"Executing: {command}")
    try:
        # 'vsh -c <command>' is the standard way to execute a command string.
        return subprocess.check_output(['vsh', '-c', command]).decode('utf-8')
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error executing command with 'vsh': {e}")
        print("This script requires the 'vsh' command to be available in the system's PATH.")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def bounce_interface(interface):
    """Performs a shutdown and no shutdown on the specified interface."""
    print(f"--- Bouncing interface {interface} ---")
    execute_command(f"conf t ; interface {interface} ; shutdown")
    print(f"Interface {interface} is shut down.")
    execute_command(f"conf t ; interface {interface} ; no shutdown")
    print(f"Interface {interface} is enabled.")

def check_ping(ip_address, vrf, count=1):
    """
    Sends a number of pings to the specified IP in the given VRF.
    Returns True if any ping is successful, False otherwise.
    """
    print(f"--- Pinging {ip_address} in VRF {vrf} ---")
    command = f"ping {ip_address} vrf {vrf} count {count}"
    try:
        output = execute_command(command)
        # A successful ping on a Nexus contains '!' in the output.
        # The previous logic incorrectly checked for the ABSENCE of "0.00% packet loss".
        return "!" in output
    except subprocess.CalledProcessError:
        # This exception is raised by check_output if the command returns a non-zero
        # exit code, which a failed ping does. We catch it and return False.
        print("Ping command failed with a non-zero exit code.")
        return False
    except Exception as e:
        # Catch any other unexpected errors during the ping.
        print(f"An unexpected error occurred during ping: {e}")
        return False

def verify_interface_status(interface, timeout=60):
    """
    Verifies that the interface is in an 'up' state.
    Waits for the interface to come up for a specified timeout period.
    """
    print(f"--- Verifying status for interface {interface} ---")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output = execute_command(f"show interface {interface} status")
            # A typical output line for an up interface is: 'Eth1/1  --  up  ...'
            for line in output.strip().split('\n'):
                if line.startswith(interface):
                    parts = line.split()
                    if len(parts) > 2:
                        status = parts[2]
                        print(f"Current status of {interface}: {status}")
                        if status == "up":
                            print(f"SUCCESS: Interface {interface} is confirmed to be up.")
                            return True
        except Exception as e:
            print(f"Could not verify interface status: {e}")
        
        print("Interface is not up yet. Waiting...")
        time.sleep(5)
    
    print(f"ERROR: Interface {interface} did not come up within {timeout} seconds.")
    return False

def main():
    """Main function to execute the script logic."""
    parser = argparse.ArgumentParser(
        description="A Python script for Cisco Nexus 9000 to bounce an interface and test connectivity."
    )
    parser.add_argument("interface", help="The interface to manage (e.g., Ethernet1/1).")
    parser.add_argument("ip_address", help="The IP address to ping.")
    parser.add_argument("vrf", help="The VRF name to use for the ping.")
    parser.add_argument("delay", type=int, help="The delay in seconds to wait for a successful ping.")
    
    args = parser.parse_args()

    print("--- Starting Interface Test Script ---")
    print(f"Configuration: Interface={args.interface}, IP={args.ip_address}, VRF={args.vrf}, Delay={args.delay}s")

    # 1. Initial interface bounce
    bounce_interface(args.interface)

    # 2. Monitor and ping during the delay period
    print(f"\n--- Entering {args.delay}s monitoring period ---")
    ping_successful = False
    start_time = time.time()
    
    while time.time() - start_time < args.delay:
        if check_ping(args.ip_address, args.vrf):
            print(f"SUCCESS: Ping to {args.ip_address} was successful.")
            ping_successful = True
            break
        else:
            print(f"Ping failed. Retrying in 5 seconds...")
            time.sleep(5)

    # 3. Conditional second bounce
    if ping_successful:
        print("\nPing was successful. Performing second interface bounce.")
        bounce_interface(args.interface)
    else:
        print(f"\nFAILURE: Ping to {args.ip_address} was not successful within the {args.delay}s delay.")
        print("--- Script finished with no further action ---")
        return

    # 4. Final verification
    print("\n--- Final Verification Step ---")
    verify_interface_status(args.interface)
    
    print("\n--- Script finished successfully ---")

if __name__ == "__main__":
    main()