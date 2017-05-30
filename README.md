#!/usr/bin/python
import os, sys, subprocess, shlex, re, fnmatch, signal
from subprocess import call
import smtplib
import threading
import time
import MySQLdb as mdb
def send_mail_gmail(fromaddrs,toaddrs,subject,text):
        msg = """\
From: %s
To: %s
Subject: %s

%s
""" % (fromaddrs, ", ".join(toaddrs), subject, text)
        username = 'monitor.iptv'
        password = 'hutieug0'
        server = smtplib.SMTP('smtp.gmail.com:587')  
        server.starttls()  
        server.login(username,password)  
        server.sendmail(fromaddrs, toaddrs, msg)  
        server.quit()
def connect_mysql_db(host,port,user,password,db):
        return mdb.connect(host=host,port=port,user=user,passwd=password,db=db);
def close_mysql_db(con):
        return con.close();
def ffmpeg_wall(source,file_image):
#    cmnd = ['/usr/local/bin/ffprobe', source, '-v', 'quiet' , '-show_format', '-show_streams']
        cmnd = ['/opt/ffmpeg/ffmpeg','-timeout','60','-i', source, '-v', 'quiet','-r','1','-f','image2',file_image]
        p = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timeout = 60
        i = 0
        while p.poll() is None:
                time.sleep(1)
                i+=1
                if i > timeout:
                        os.kill(p.pid, signal.SIGKILL)
def check_probe(profile,session,value,id):
        file_image="/var/www/html/images/channel/id.%d.jpg" % (id)
        file_logo="/var/www/html/images/logo/logo.%d." % (id) + '%d.jpg'
        file_default="/var/www/html/images/channel/error.jpg"
#       print file_image
        if os.path.isfile(file_image):
                os.remove(file_image)
        ffmpeg_wall(profile,file_image);
        if ( not os.path.isfile(file_image)):
                cmd="cp %s %s" % (file_default,file_image)
                os.system(cmd)
        else:
                cmd="convert %s" % (file_image) + ' -crop 25%x25%@' + " %s" % (file_logo)
                os.system(cmd)
#       print "status=" + str(status) + ":value=" + str(value) + ":"
#probe_file('udp://@225.1.1.160:30120')
host='localhost';
port=3306;
user='M0admin';
password='M0admin';
db='monitor'
session=connect_mysql_db(host,port,user,password,db);
cur=session.cursor();
cur.execute("select p.id,c.name,p.ip,p.status,SUM(case when pg.group_id=34 then 1 when pg.group_id=36 then 5 when pg.group_id=38 then 10  end) as group_name from profile as p, channel as c,monitor.group as g, profile_group as pg where p.channel_id=c.id and pg.profile_id=p.id and pg.group_id=g.id and pg.group_id in (34,36, 38) group by p.ip order by c.name,p.id");
rows = cur.fetchall();
for row in rows:
        while threading.activeCount() > 5:
#               print str(count)
                time.sleep(1);
        mysql=connect_mysql_db(host,port,user,password,db);
        t = threading.Thread(target=check_probe, args=('udp://@'+row[2],mysql,row[3],row[0],))
        t.start();
time.sleep(90)
