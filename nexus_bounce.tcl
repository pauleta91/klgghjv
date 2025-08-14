#!/usr/bin/tclsh

proc ping_target {target_ip} {
    set result [catch {exec ping -c 1 -W 2 $target_ip} output]
    return [expr {$result == 0}]
}

proc shut_interface {interface} {
    set result [catch {
        exec cli "configure terminal ; interface $interface ; shutdown"
    } output]
    
    if {$result == 0} {
        puts "Interface $interface shut down"
        return 1
    } else {
        puts "Error shutting interface: $output"
        return 0
    }
}

proc no_shut_interface {interface} {
    set result [catch {
        exec cli "configure terminal ; interface $interface ; no shutdown"
    } output]
    
    if {$result == 0} {
        puts "Interface $interface brought up"
        return 1
    } else {
        puts "Error bringing up interface: $output"
        return 0
    }
}

proc main {} {
    global argc argv
    
    if {$argc != 3} {
        puts "Usage: tclsh nexus_bounce.tcl <interface> <target_ip> <delay_seconds>"
        puts "Example: tclsh nexus_bounce.tcl Ethernet1/1 10.1.1.1 5"
        exit 1
    }
    
    set interface [lindex $argv 0]
    set target_ip [lindex $argv 1]
    set delay [lindex $argv 2]
    
    puts "Starting bounce cycle for interface $interface"
    puts "Monitoring ping to $target_ip"
    puts "Delay between operations: $delay seconds"
    
    set cycle_count 0
    
    # Handle Ctrl+C gracefully
    signal trap SIGINT {
        puts "\nScript interrupted by user"
        puts "Ensuring interface is up before exit..."
        no_shut_interface $::interface
        exit 0
    }
    
    while {1} {
        incr cycle_count
        puts "\n--- Cycle $cycle_count ---"
        
        if {[ping_target $target_ip]} {
            puts "Ping to $target_ip successful - continuing bounce cycle"
            
            if {[shut_interface $interface]} {
                after [expr {$delay * 1000}]
                
                if {[no_shut_interface $interface]} {
                    after [expr {$delay * 1000}]
                } else {
                    puts "Failed to bring up interface - stopping"
                    break
                }
            } else {
                puts "Failed to shut interface - stopping"
                break
            }
        } else {
            puts "Ping to $target_ip failed - stopping bounce cycle"
            no_shut_interface $interface
            break
        }
    }
}

main