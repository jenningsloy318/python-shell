#!/usr/bin/env python3
import os
import paramiko
import sys
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import argparse
import time
import datetime
import socket
from dateutil.relativedelta import relativedelta
def cmdgen():
    global cmd_list
    current_time=datetime.datetime.now()
    monthdelta=relativedelta(months=-1)
    #monthdelta=datetime.timedelta(days=-30)
    #yeardelta=datetime.timedelta(days=-365)
    yeardelta=relativedelta(years=-1)
    time_1_month_ago=current_time+monthdelta
    time_2_month_ago=time_1_month_ago+monthdelta
    time_3_month_ago=time_2_month_ago+monthdelta
    time_4_month_ago=time_3_month_ago+monthdelta
    time_5_month_ago=time_4_month_ago+monthdelta
    time_6_month_ago=time_4_month_ago+monthdelta
    last_year=current_time+yeardelta
    grep_month=time_1_month_ago.strftime('%Y-%b')+'|'+time_2_month_ago.strftime('%Y-%b')+'|'+time_3_month_ago.strftime('%Y-%b')+'|'+time_4_month_ago.strftime('%Y-%b')+'|'+time_5_month_ago.strftime('%Y-%b')+'|'+time_6_month_ago.strftime('%Y-%b')
    grep_year=current_time.strftime('%Y')+'|'+last_year.strftime('%Y')
    local_accts='''getent --service=files passwd | awk -F: '{print$1}' '''
    cmd_lastlog='last -F -w '+'|'+'grep -E -v "down|eboot"'+'|'+'grep -E "'+grep_year+'"'+'|'+'awk '''''{print $1,$8"-"$5}'''+"'"+'|grep -E "'+grep_month+'"'+'|sort -k1|'+'awk '''''{print $1}'''+"'"+'|uniq -c|'+'awk ''''-v HOSTNAME=`hostname` -v local_accts="`getent --service=files passwd | awk -F: '{print$1}'`"  '{if(local_accts~$2){print HOSTNAME","$2","$1",Local";}else{print HOSTNAME","$2","$1",LDAP";}}'''+"'" 
    cmd_lastlog_accts='login_accts=`last -F -w '+'|'+'grep -E -v "down|eboot"'+'|'+'grep -E "'+grep_year+'"'+'|'+'awk '''''{print $1,$8"-"$5}'''+"'"+'|grep -E "'+grep_month+'"'+'|sort -k1|'+'awk '''''{print $1}'''+"'"+'|uniq -c|'+'awk '''''{print $2}'''+"'`"
    cmd_lastlog_title='echo "Server_IP,Hostname,Acct,Number of Acct access,Type"'
    cmd_non_OS_acct='cat /etc/passwd| egrep -v "abrt|nfsnobody|saslauth|rabbitmq|mysql|nrpe|clam|memcached|rrdcached|nagios|redis|ntop|vpn|zenoss|dovenull|mapred|zookeeper|impala|noaccess|nobody|ftp|ssh|avahi|false|nologin" |'+'awk -F: '''''{ if ( $3 > 100 ) print  $1}'''+"'"
    cmd_non_OS_acct_title='echo "Server_IP,Non OS accts"'
    cmd_non_local_access=cmd_lastlog_accts+';for acct in `getent --service=files passwd| egrep -v "abrt|nfsnobody|saslauth|rabbitmq|mysql|nrpe|clam|memcached|rrdcached|nagios|redis|ntop|vpn|zenoss|dovenull|mapred|zookeeper|impala|noaccess|nobody|ftp|ssh|avahi|false|nologin"'+'|awk -F: '''''{ if ( $3 > 100 ) print  $1}'''+"'`;"+'do echo $login_accts|grep -q $acct;[ $? -ne 0 ] && echo "$HOSTNAME,$acct,0,Local" ; done'
    cmd_non_ldap_access=cmd_lastlog_accts+';for acct in `getent --service=ldap passwd| egrep -v "abrt|nfsnobody|saslauth|rabbitmq|mysql|nrpe|clam|memcached|rrdcached|nagios|redis|ntop|vpn|zenoss|dovenull|mapred|zookeeper|impala|noaccess|nobody|ftp|ssh|avahi|false|nologin"'+'|awk -F: '''''{ if ( $3 > 100 ) print  $1}'''+"'`;"+'do echo $login_accts|grep -q $acct;[ $? -ne 0 ] && echo "$HOSTNAME,$acct,0,LDAP" ; done'
    cmd_non_access_title='echo "Server_IP,No Access"'
    #cmd_list=[cmd_non_OS_acct_title,cmd_non_OS_acct,cmd_lastlog_title,cmd_lastlog,cmd_non_access_title,cmd_non_access]
    cmd_list=[cmd_lastlog_title,cmd_lastlog,cmd_non_local_access,cmd_non_ldap_access]
    print(cmd_lastlog_title)
    print(cmd_lastlog)
    print(local_accts)
    print(cmd_non_local_access)
    print(cmd_non_ldap_access)
def sshcmd(server):
    try:
        print("Start to process "+server.rstrip()+"\n")
        log_sshdcmd=open("/tmp/."+server.rstrip()+".log","w")
        #log_sshdcmd.write("\n"+server.rstrip()+":Start to process "+server.rstrip()+"\n\n")
        sshconn= paramiko.SSHClient()
        sshconn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sshconn.connect(hostname=server,username=user,password=passwd,timeout=10)
        for cmd in cmd_list:
            stdin, stdout, stderr = sshconn.exec_command(cmd)
            if "Server_IP" in cmd:
                for line in stdout.readlines():
                    log_sshdcmd.write(line)
            else:
                for line in stdout.readlines():
                    log_sshdcmd.write(server.rstrip()+","+line)
        #log_sshdcmd.write("\n")
        sshconn.close()
        print("Process "+server.rstrip()+" successfully \n")
        #log_sshdcmd.write(server.rstrip()+":Process "+server.rstrip()+" successfully \n")
        #log_sshdcmd.write("--------------------------------------------------------- \n")
        log_sshdcmd.flush()
        log_sshdcmd.close()
        return True
    except paramiko.AuthenticationException as s:
        print(server.rstrip(),s.__str__(),"\n")
        #log_sshdcmd.write(server.rstrip()+" "+s.__str__()+"\n")
        print("Process "+server.rstrip()+" failed \n")
        #log_sshdcmd.write(server.rstrip()+":Process "+server.rstrip()+" failed \n")
        #log_sshdcmd.write("--------------------------------------------------------- \n")
        log_sshdcmd.flush()
        log_sshdcmd.close()
        return False
    except paramiko.SSHException as p:
        print(server.rstrip(),p.__str__(),"\n")
        #log_sshdcmd.write(server.rstrip()+" "+p.__str__()+"\n")
        print("Process "+server.rstrip()+" failed \n")
        #log_sshdcmd.write(server.rstrip()+":Process "+server.rstrip()+" failed \n")
        #log_sshdcmd.write("--------------------------------------------------------- \n")
        log_sshdcmd.flush()
        log_sshdcmd.close()
        return False
    except socket.error as t:
        print(server.rstrip(),t.__str__(),"\n")
        #log_sshdcmd.write(server.rstrip()+" "+t.__str__()+"\n")
        print("Process "+server.rstrip()+" failed \n")
        #log_sshdcmd.write(server.rstrip()+":Process "+server.rstrip()+" failed \n")
        #log_sshdcmd.write("--------------------------------------------------------- \n")
        log_sshdcmd.flush()
        log_sshdcmd.close()
        return False
def main():
    global log_global_file,user,passwd
    arguments = argparse.ArgumentParser()  
    arguments.add_argument("-s","--server_list",nargs="?",help="The servers list",required=True)
    arguments.add_argument("-l","--log", nargs="?",help="The log file,default result.log",default="result.log")
    if len(sys.argv) ==1:
        arguments.print_help()
        sys.exit(1)
    args = arguments.parse_args()
    server_list = open(args.server_list)
    log_global_file =args.log
    timestamp=time.strftime("%Y%m%d%H%M")
    user=''
    passwd=''
    if os.path.exists(log_global_file):
        os.rename(log_global_file,log_global_file+"."+timestamp)
    hosts=server_list.readlines()
    start_time=datetime.datetime.now()
    print(start_time)
    cmdgen()
    pool = ThreadPool(20)
    pool.map(sshcmd,hosts)
    pool.close()
    pool.join()
    log_global=open(log_global_file,"w")
    for host in hosts:
        if os.path.exists("/tmp/."+host.rstrip()+".log"):
        	for line in open("/tmp/."+host.rstrip()+".log").readlines():
            		log_global.write(line)
        	os.remove("/tmp/."+host.rstrip()+".log")
    log_global.close()
    server_list.close()
    end_time=datetime.datetime.now()
    print(end_time)
    exit(0)
if __name__ == "__main__":
    main()
