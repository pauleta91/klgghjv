
import time
import argparse
def get_command_executor():
    """
    Dynamically finds the correct function for executing CLI commands on a Nexus switch.
    Tries multiple common methods to ensure compatibility across NX-OS versions.
    """
    # Method 1: from cli import cli
    try:
        from cli import cli
        print("Using 'from cli import cli'")
        return cli
    except ImportError:
        pass

    # Method 2: from cisco.cli import cli
    try:
        from cisco.cli import cli
        print("Using 'from cisco.cli import cli'")
        return cli
    except ImportError:
        pass

    # Method 3: from cisco import vsh
    try:
        from cisco import vsh
        print("Using 'from cisco import vsh'")
        return vsh
    except ImportError:
        pass
        
    # Fallback for local testing
    print("Warning: No native Cisco CLI module found. Using mock function for local testing.")
    def mock_cli(command):
        print(f"MOCK Executing: '{command}'")
        if "ping" in command and "1.1.1.1" in command:
            import subprocess

def execute_command(command):
    """
    Executes a CLI command on the Nexus switch by calling the 'vsh' executable
    directly as a subprocess.
    """
    print(f"Executing: {command}")
    try:
        # The working script uses subprocess to call 'vsh'. We will adopt that method.
        # 'vsh -c <command>' is the standard way to execute a command string.
        return subprocess.check_output(['vsh', '-c', command]).decode('utf-8')
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error executing command with 'vsh': {e}")
        print("This script requires the 'vsh' command to be available in the system's PATH.")
        # We will exit if the command execution fails, as the script cannot proceed.
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise
        if "show interface" in command and "status" in command:
            return "--------------------------------------------------------------------------------\nPort          Name               Status    Vlan      Duplex  Speed   Type\n--------------------------------------------------------------------------------\nEth1/1        --                 up        1         full    1G      --\n"
        return ""
    return mock_cli

# Discover the correct command executor when the script starts
execute_command_on_switch = get_command_executor()

def execute_command(command):
    """Executes a CLI command using the discovered function and returns the output."""
    print(f"Executing: {command}")
    output = execute_command_on_switch(command)
    time.sleep(1)  # Give the system a moment to process the command
    return output




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
    # On Nexus, a successful ping response typically includes '!' characters.
    # We check for at least one successful packet.
    output = execute_command(f"ping {ip_address} vrf {vrf} count {count}")
    return "!" in output and "0.00% packet loss" not in output

def verify_interface_status(interface, timeout=60):
    """
    Verifies that the interface is in an 'up' state.
    Waits for the interface to come up for a specified timeout period.
    """
    print(f"--- Verifying status for interface {interface} ---")
    start_time = time.time()
    while time.time() - start_time < timeout:
        # The command 'show interface <name> status' is a reliable way to check
        output = execute_command(f"show interface {interface} status")
        # A typical output line for an up interface is: 'Eth1/1  --  up  ...'
        # We split the line and check the status field.
        for line in output.strip().split('\n'):
            if line.startswith(interface):
                parts = line.split()
                status = parts[2]
                print(f"Current status of {interface}: {status}")
                if status == "up":
                    print(f"SUCCESS: Interface {interface} is confirmed to be up.")
                    return True
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
