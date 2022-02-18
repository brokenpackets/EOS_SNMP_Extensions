#!/usr/bin/python -u
# To-Do: Update doc
# 2. Copy snmp_passpersist.py to /mnt/flash
# 3. Enable protocol unix-socket on eapi with:
#      management api http-commands
#         no shutdown
#         protocol unix-socket
# 4. Configure snmp to respond to the custom OID
#        snmp-server extension .1.3.6.1.4.1.8072.2.1000 flash:/snmp_AssetTag.py
#
# Example Output:
# sudo snmpwalk -v2c -c public -m localhost .1.3.6.1.4.1.8072.2.1000
#    NET-SNMP-EXAMPLES-MIB::netSnmpExamples.1000.0.1.1.1 = INTEGER: 0


import snmp_passpersist as snmp
import sys, os, errno
import Logging
from jsonrpclib import Server
import re

# Configuration section
OID_BASE = ".1.3.6.1.4.1.8072.2.1000"
POLLING_INTERVAL = 60
MAX_RETRY = 10
COMMAND = 'show hardware asset-tag'

pp = None

# Define log messages
Logging.logD( id="SNMP_EXTENSION",
              severity=Logging.logInfo,
              format="%s",
              explanation="Status message from snmp extension file",
              recommendedAction=Logging.NO_ACTION_REQUIRED
)

def grabTag():
   switch = Server( "unix:/var/run/command-api.sock" )
   response = switch.runCmds( 1, [ COMMAND ])[0]['assets']['switch']['tag']
   return response

def run_command():
   tag = grabTag()
   oid = '0.1.'
   pp.add_str(oid+'1.' + '1', tag)

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
