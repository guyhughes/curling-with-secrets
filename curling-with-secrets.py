#!/usr/bin/env python3.3

#  Guy Hughes, 2014
#  GNU General Public License Version 3, 29 June 2007

from sys import stdin
from sys import stdout
import os
import argparse
#from sys import os.environ
#from sys import os.access
#from sys import os.mkdirs
#from sys import os.path
import subprocess
import errno
import getpass

def init():
    global args
    global secretfile
    global secretfiledir
    # parse args
    parser = argparse.ArgumentParser(description='This is curling-with-secrets by Guy Hughes.')
    parser.add_argument('--secretfile',nargs='?',help='specify an alternative secret file',type=str)
    parser.add_argument('user', help='the username to pass to curl',type=str)
    parser.add_argument('url', help='the url to pass to curl',type=str)
    args=parser.parse_args()
    #secretfile=os.path.abspath(os.environ.get('XDG_CONFIG_HOME',os.environ.get('HOME') + "/.config") + "/secretcurl/secret.enc")
    if args.secretfile:
        secretfile = os.path.abspath(args.secretfile)
    else:
        secretfile=os.path.abspath('./secret.enc')
        secretfiledir=os.path.dirname(secretfile)

    if check():
        curl()

def check():
    if os.path.isfile(secretfile) and os.access(secretfile, os.R_OK):
        print("I found secretfile at %s. [OK]" % secretfile)
        return True
    else:
        print("I did not find the secretfile at %s. We'll now create it..." % secretfile)
        return createfile()

def token():
    echop=subprocess.Popen(["echo", secretfile], stdout=subprocess.PIPE)
    shap=subprocess.Popen(['sha512sum'],stdout=subprocess.PIPE,stdin=echop.stdout)
    grepp=subprocess.Popen(['grep', '-Eo','\'^.{40}\''],stdout=subprocess.PIPE,stdin=shap.stdout)
    echop.stdout.close()
    shap.stdout.close()
    result=grepp.communicate()[0]
    return result


def createfile():
    # safety check
    if os.path.isfile(secretfile):
        print("FATAL: secretfile exists at %s" % secretfile)
        print("Stopping, to prevent secretfile from being overriden.")
        print("If you wish to overwrite the secretfile, first delete it yourself this run this command again.")
        exit(1)

    print("Creating the secretfile at %s" % secretfile)
    print("Remember: Once the secret file is created, this script"
          " will only be able to decrypt while it is in the same directory and filename."
          "If you ever wish to rename the secretfile, you'd need to modify this script "
          "or recreate the secretfile using this script.")
    
    print("Checking for directory %s" % secretfiledir)
    if not os.path.exists(secretfiledir):
        sys.stdout.write("Making directories...")
        os.makedirs(secretfiledir, exist_ok=True)
    else:
        print("Parent directories are OK")

    print("Please enter the secret password to be passed to curl:")
    password=getpass.getpass()
    thetoken = token()
    echop=subprocess.Popen(['echo',password],stdout=subprocess.PIPE)
    opensslp=subprocess.Popen(['openssl', 'enc', '-aes-256-cbc',
                     '-salt', '-a',
                     '-k', thetoken,
                     '-out', secretfile
                     ], stdin=echop.stdout)
    echop.stdout.close()
    
    del password
    del thetoken
    
    print("Createfile done.")
    return True

def curl():
    print("Decrypting the password...")
    thetoken=token()
    opensslp=subprocess.Popen(['openssl','enc','-aes-256-cbc','-d', '-a','-k',thetoken,
                                      '-in', secretfile],stdout=subprocess.PIPE)
    password=opensslp.communicate()[0].decode('utf-8')
    print(args)
    print(args.url)
    print(password)
    curlconfig="user = " + args.user + "\:" + password  + "\nurl = " + args.url
    curlp=subprocess.Popen(['curl','--basic', '-K', '-'],
                          stdin=subprocess.PIPE,stderr=subprocess.STDOUT,shell=False)
    result=curlp.communicate(input=bytes(curlconfig, 'UTF-8'))
    print(result)

    

    del password



init()
