#!/usr/bin/python -u
# 1. Copy this script to /mnt/flash
# 2. Copy snmp_passpersist.py to /mnt/flash
# 3. Configure snmp to respond to the custom OID
#        snmp-server extension .1.3.6.1.4.1.8072.2.1000 flash:/mcast-snmpexample.py
#
# Example Output:
# sudo snmpwalk -v2c -c public -m localhost .1.3.6.1.4.1.8072.2.1000
#    NET-SNMP-EXAMPLES-MIB::netSnmpExamples.1000.0.1.1.1 = INTEGER: 0
#    NET-SNMP-EXAMPLES-MIB::netSnmpExamples.1000.0.1.1.2 = INTEGER: 0

import snmp_passpersist as snmp
import sys, os, errno
import Logging
from jsonrpclib import Server
import re

# Configuration section
OID_BASE = ".1.3.6.1.4.1.8072.2.1000"
POLLING_INTERVAL = 60
MAX_RETRY = 10
COMMAND = 'show cpu counters queue summary | grep CoppSystemIpMcast'

pp = None

# Define log messages
Logging.logD( id="SNMP_EXTENSION",
              severity=Logging.logInfo,
              format="%s",
              explanation="Status message from snmp extension file",
              recommendedAction=Logging.NO_ACTION_REQUIRED
)

def grabCounters():
   switch = Server( "unix:/var/run/command-api.sock" )
   response = switch.runCmds( 1, [ COMMAND ], 'text')[0]['output']
   return response

def mcastQueue(counters):
   mcastCounters = counters.split('\n')[0]
   dropCounter = mcastCounters.split()[3]
   return dropCounter

def mcastMissQueue(counters):
   mcastMissCounters = counters.split('\n')[1]
   dropCounter = mcastMissCounters.split()[3]
   return dropCounter

def run_command():
   counters = grabCounters()
   oid = '0.1.'
   pp.add_str(oid+'1.' + '1', mcastQueue(counters))
   pp.add_str(oid+'1.' + '2', mcastMissQueue(counters))

def main():
   global pp
   retry_counter = MAX_RETRY
   while retry_counter > 0:
      try:
          Logging.log(SNMP_EXTENSION,"snmp extension script starting")
          pp=snmp.PassPersist(OID_BASE)
          pp.start(run_command,POLLING_INTERVAL)
      # Handle possible errors starting the script
      except KeyboardInterrupt:
          Logging.log(SNMP_EXTENSION,"Exiting on user request")
          sys.exit(0)
      except IOError, e:
          if e.errno == errno.EPIPE:
              Logging.log(SNMP_EXTENSION,"snmpd has closed the pipe")
              sys.exit(0)
          else:
              Logging.log(SNMP_EXTENSION,"updater thread has died: %s" %e)
      except Exception, e:
          Logging.log(SNMP_EXTENSION,"main thread has died %s: %s" % (e.__class__.__name__, e))
      else:
          Logging.log(SNMP_EXTENSION,"updater thread has died %s: %s" % (e.__class__.__name__, e))
      retry_counter-=1
   Logging.log(SNMP_EXTENSION,"too many retries, exiting")
   sys.exit(1)

if __name__ == '__main__':
   main()
