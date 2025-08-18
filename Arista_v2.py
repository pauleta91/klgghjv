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
        format='%(asctime)s - %(levelname)s - %(message)s',
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
    logger.info(f"Shutting down interface {interface}")
    run_cli(f"conf;interface {interface};shutdown")

def no_shut(interface):
    logger = logging.getLogger(__name__)
    logger.info(f"Bringing up interface {interface}")
    run_cli(f"conf;interface {interface};no shutdown")

def bounce(interface):
    logger = logging.getLogger(__name__)
    logger.info(f"Bouncing interface {interface}")
    shut(interface)
    no_shut(interface)

def int_up(interface, timeout=30):
    logger = logging.getLogger(__name__)
    logger.info(f"Waiting for interface {interface} to come up (timeout: {timeout}s)")
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
    logger.info(f"Pinging {ip} in VRF {vrf} from management1")
    output = run_cli(f'ping {ip} vrf {vrf} count 2 source management1')
    if "0 received" in output:
        logger.warning(f"Ping to {ip} in VRF {vrf} failed")
        return False 
    logger.info(f"Ping to {ip} in VRF {vrf} successful")
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
    try:
        while True:
            cycle += 1
            logger.info(f"Starting cycle {cycle}")
            success = False

            for attempt in range(1, 4):
                logger.info(f"Flap attempt {attempt} of 3")
                bounce(args.interface)

                int_up(args.interface)

                if ping(args.ip_address, args.vrf):
                    logger.info(f"Cycle {cycle} completed successfully after {attempt} attempts")
                    success = True
                    break
                else:
                    logger.warning(f"Ping failed on attempt {attempt}")

            if not success:
                logger.error("Ping failed after 3 attempts. Exiting script.")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Script interrupted by user. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()
