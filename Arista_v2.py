#!/usr/bin/env python3
import time
import sys
import argparse
import subprocess
import logging
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(f'arista_bounce_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_cli(command):
    logger = logging.getLogger(__name__)
    payload = (command.replace(";", r"\n"))
    cmd = f"Cli -p15 -c $'{payload}'"
    logger.debug(f"Executing CLI command: {command}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stderr:
        logger.warning(f"CLI command stderr: {result.stderr.strip()}")
    return result.stdout

def shut(interface):
    logger = logging.getLogger(__name__)
    logger.debug(f"Shutting down interface {interface}")
    run_cli(f"conf;interface {interface};shutdown")

def no_shut(interface):
    logger = logging.getLogger(__name__)
    logger.debug(f"Bringing up interface {interface}")
    run_cli(f"conf;interface {interface};no shutdown")

def bounce(interface):
    logger = logging.getLogger(__name__)
    logger.info(f"Bouncing interface {interface}")
    shut(interface)
    no_shut(interface)

def int_up(interface, timeout=30):
    logger = logging.getLogger(__name__)
    logger.debug(f"Waiting for interface {interface} to come up (timeout: {timeout}s)")
    start = time.time()
    while time.time() - start < timeout:
        output = run_cli(f"show interfaces {interface} | include connected")
        if "connected" in output:
            elapsed = time.time() - start
            logger.info(f"Interface {interface} is connected after {elapsed:.1f}s")
            return True
        time.sleep(1)
    logger.warning(f"Interface {interface} did not come up within {timeout}s timeout")
    return False
def ping(ip, vrf):
    logger = logging.getLogger(__name__)
    logger.debug(f"Pinging {ip} in VRF {vrf} from management1")
    output = run_cli(f'ping {ip} vrf {vrf} count 2 source management1')
    if "0 received" in output:
        logger.debug(f"Ping to {ip} in VRF {vrf} failed")
        return False 
    logger.debug(f"Ping to {ip} in VRF {vrf} successful")
    return True

def main():
    logger = setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("interface", help="Interface to flap")
    parser.add_argument("ip_address", help="IP address to ping")
    parser.add_argument("vrf", help="VRF to use for ping")
    args = parser.parse_args()

    logger.info(f"Starting Arista interface bounce script")
    logger.info(f"Interface: {args.interface}, Target IP: {args.ip_address}, VRF: {args.vrf}")

    cycle = 0
    successful_cycles = 0
    total_recovery_time = 0
    script_start_time = time.time()
    
    try:
        while True:
            cycle += 1
            cycle_start_time = time.time()
            logger.info(f"Starting cycle {cycle}")

            bounce(args.interface)
            
            interface_up_success = int_up(args.interface)
            if not interface_up_success:
                logger.error(f"Interface {args.interface} failed to come up within timeout. Exiting.")
                print_final_stats(cycle, successful_cycles, total_recovery_time, script_start_time)
                sys.exit(1)
            
            ping_attempts = 0
            max_ping_attempts = 5
            while not ping(args.ip_address, args.vrf):
                ping_attempts += 1
                if ping_attempts >= max_ping_attempts:
                    logger.error(f"Ping failed {max_ping_attempts} times. Exiting.")
                    print_final_stats(cycle, successful_cycles, total_recovery_time, script_start_time)
                    sys.exit(1)
                logger.warning(f"Ping failed (attempt {ping_attempts}/{max_ping_attempts}), waiting 10 seconds before retry...")
                time.sleep(10)
            
            cycle_time = time.time() - cycle_start_time
            total_recovery_time += cycle_time
            successful_cycles += 1
            
            logger.info(f"Cycle {cycle} completed successfully in {cycle_time:.1f}s")
            
            # Print periodic stats every 10 cycles
            if cycle % 10 == 0:
                success_rate = (successful_cycles / cycle) * 100
                avg_recovery = total_recovery_time / successful_cycles if successful_cycles > 0 else 0
                print(f"\n--- Stats after {cycle} cycles ---")
                print(f"Success rate: {success_rate:.1f}% | Avg recovery: {avg_recovery:.1f}s\n")

    except KeyboardInterrupt:
        logger.info("Script interrupted by user. Exiting.")
        print_final_stats(cycle, successful_cycles, total_recovery_time, script_start_time)
        sys.exit(0)

def print_final_stats(total_cycles, successful_cycles, total_recovery_time, script_start_time):
    logger = logging.getLogger(__name__)
    runtime = time.time() - script_start_time
    success_rate = (successful_cycles / total_cycles) * 100 if total_cycles > 0 else 0
    avg_recovery = total_recovery_time / successful_cycles if successful_cycles > 0 else 0
    
    print("\n" + "="*50)
    print("           FINAL STATISTICS")
    print("="*50)
    print(f"Total runtime:       {runtime/60:.1f} minutes")
    print(f"Total cycles:        {total_cycles}")
    print(f"Successful cycles:   {successful_cycles}")
    print(f"Success rate:        {success_rate:.1f}%")
    print(f"Average recovery:    {avg_recovery:.1f}s")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
