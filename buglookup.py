
import cisco
import time
import re

# --- START OF CONFIGURATION ---

# The interface you want to flap (e.g., 'Ethernet1/1')
INTERFACE_NAME = 'Ethernet1/48'

# The IP address to ping to check for connectivity.
TARGET_IP = '8.8.8.8'

# Delay in seconds between flaps to prevent port-flap detection.
# Nexus default is 5 flaps in 10 seconds to trigger an event.
# A value of 3-5 seconds is safe. DO NOT SET TO 0.
DELAY_SECONDS = 5

# --- END OF CONFIGURATION ---

def check_ping_success(ping_output):
    """
    Parses the output of a ping command to check for success.
    Returns True if successful, False otherwise.
    """
    # A successful ping on NX-OS will contain a line like:
    # "1 packets transmitted, 1 packets received, 0.00% packet loss"
    match = re.search(r"(\d+)\s+packets\s+transmitted,\s+(\d+)\s+packets\s+received", ping_output)
    if match:
        transmitted, received = map(int, match.groups())
        if transmitted > 0 and received > 0:
            return True
    return False

def main():
    """
    Main function to run the interface flap logic.
    """
    print(f"--- Starting Interface Flap Script ---")
    print(f"Interface: {INTERFACE_NAME}")
    print(f"Target IP: {TARGET_IP}")
    print(f"Delay:     {DELAY_SECONDS} seconds")
    print("------------------------------------")
    print("Press Ctrl+C to stop the script manually.")

    try:
        while True:
            # Step 1: Ping the target IP
            print(f"Pinging {TARGET_IP}...")
            ping_command = f'ping {TARGET_IP} count 1'
            try:
                ping_output = cisco.cli.cli(ping_command)
                
                # Step 2: Check if ping was successful
                if check_ping_success(ping_output):
                    print(f"Ping successful. Flapping interface {INTERFACE_NAME}.")
                    
                    # Step 3: Flap the interface
                    config_commands = [
                        f'interface {INTERFACE_NAME}',
                        'shutdown',
                        'no shutdown'
                    ]
                    cisco.cli.configurep(config_commands)
                    print(f"Interface {INTERFACE_NAME} flapped successfully.")
                    
                else:
                    print(f"Ping to {TARGET_IP} failed. Stopping script.")
                    print("--- Script Finished ---")
                    break

            except cisco.cli.CLIError as e:
                print(f"Error executing command: {e}")
                print("Stopping script due to error.")
                break

            # Step 4: Wait for the specified delay
            print(f"Waiting for {DELAY_SECONDS} seconds...")
            time.sleep(DELAY_SECONDS)

    except KeyboardInterrupt:
        print("\nScript stopped by user (Ctrl+C).")
        print("--- Script Finished ---")

if __name__ == '__main__':
    main()
