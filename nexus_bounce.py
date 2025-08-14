#!/isan/bin/python

import time
import subprocess
import sys

def ping_target(target_ip):
    try:
        result = subprocess.call(['ping', '-c', '1', '-W', '2', target_ip], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
        return result == 0
    except:
        return False

def shut_interface(interface):
    try:
        cli_cmd = 'configure terminal ; interface {} ; shutdown'.format(interface)
        subprocess.call(['cli', cli_cmd], stdout=subprocess.DEVNULL)
        print("Interface {} shut down".format(interface))
        return True
    except Exception as e:
        print("Error shutting interface: {}".format(str(e)))
        return False

def no_shut_interface(interface):
    try:
        cli_cmd = 'configure terminal ; interface {} ; no shutdown'.format(interface)
        subprocess.call(['cli', cli_cmd], stdout=subprocess.DEVNULL)
        print("Interface {} brought up".format(interface))
        return True
    except Exception as e:
        print("Error bringing up interface: {}".format(str(e)))
        return False

def main():
    if len(sys.argv) != 4:
        print("Usage: python nexus_bounce.py <interface> <target_ip> <delay_seconds>")
        print("Example: python nexus_bounce.py Ethernet1/1 10.1.1.1 5")
        sys.exit(1)
    
    interface = sys.argv[1]
    target_ip = sys.argv[2]
    delay = int(sys.argv[3])
    
    print("Starting bounce cycle for interface {}".format(interface))
    print("Monitoring ping to {}".format(target_ip))
    print("Delay between operations: {} seconds".format(delay))
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            print("\n--- Cycle {} ---".format(cycle_count))
            
            if ping_target(target_ip):
                print("Ping to {} successful - continuing bounce cycle".format(target_ip))
                
                if shut_interface(interface):
                    time.sleep(delay)
                    
                    if no_shut_interface(interface):
                        time.sleep(delay)
                    else:
                        print("Failed to bring up interface - stopping")
                        break
                else:
                    print("Failed to shut interface - stopping")
                    break
            else:
                print("Ping to {} failed - stopping bounce cycle".format(target_ip))
                no_shut_interface(interface)
                break
                
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        print("Ensuring interface is up before exit...")
        no_shut_interface(interface)
    except Exception as e:
        print("Unexpected error: {}".format(str(e)))
        print("Ensuring interface is up before exit...")
        no_shut_interface(interface)

if __name__ == "__main__":
    main()