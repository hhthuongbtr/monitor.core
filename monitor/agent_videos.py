#!/usr/bin/python
import os, sys, subprocess, shlex, re, fnmatch,signal
from subprocess import call
import smtplib
import threading
import time
import MySQLdb as mdb
###-image compare#########
from PIL import Image
import math, operator
##########################
def connect_mysql_db(host,port,user,password,db):
    return mdb.connect(host=host,port=port,user=user,passwd=password,db=db);
def close_mysql_db(con):
    return con.close();
def probe_file(source,file_image):
#	cmnd = ['/usr/local/bin/ffprobe', source, '-v', 'quiet' , '-show_format', '-show_streams', '-timeout', '60']
    cmnd = ['/opt/ffmpeg/ffmpeg','-timeout','30','-i', source, '-v', 'quiet','-r','1','-f','image2',file_image,'-y']
    p = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timeout = 15
    i = 0
    while p.poll() is None:
        time.sleep(1)
        i+=1
        if i > timeout:
            os.kill(p.pid, signal.SIGKILL)
def check_probe(protocol,multicast,session,value,id,name,type,ip,video):
#	print source
    file = '/tmp/capture/image.'+str(id)+'.png'
    if os.path.isfile(file):
        image1 = Image.open(file)
    else:
        image1 = Image.open('/tmp/capture/error.png')
    h1 = image1.histogram()
    if os.path.isfile(file):
        os.remove(file)
    a = probe_file(protocol+"://"+multicast,file);
    image2 = Image.open(file)
    h2 = image2.histogram()
    rms = int(math.sqrt(reduce(operator.add,map(lambda a,b: (a-b)**2, h1, h2))/len(h1)))
    if rms < 150:
        if int(video) == 1:
            time.sleep(60);
            if os.path.isfile(file):
                os.remove(file)
            a = probe_file(protocol+"://"+multicast,file);
            image3 = Image.open(file)
            h3 = image3.histogram()
            rms = int(math.sqrt(reduce(operator.add,map(lambda a,b: (a-b)**2, h2, h3))/len(h2)))
#        print ip+"rms:"+str(rms)
            if rms < 150:
#                status = 'video error'
#                check = 2
                var=session.cursor();
                query="update profile_agent set video='0',last_update=unix_timestamp() where id='" + str(id) + "'"
                var.execute(query)
                text = """
%s %s (ip:%s) status 2 in host: %s
""" % ( name, type, multicast,ip)
                query="insert into logs (host, tag, datetime, msg) values ('" + protocol+"://"+multicast + "', 'status' ,NOW(),'" + text + "')"
#			print query
                var.execute(query)
                session.commit()
    else:
        if int(video) == 0:
            time.sleep(60);
            if os.path.isfile(file):
                os.remove(file)
            a = probe_file(protocol+"://"+multicast,file);
            image3 = Image.open(file)
            h3 = image3.histogram()
            rms = int(math.sqrt(reduce(operator.add,map(lambda a,b: (a-b)**2, h2, h3))/len(h2)))
            if rms >= 200:
#                status = 'video error'
#                check = 2
                var=session.cursor();
                query="update profile_agent set video='1',last_update=unix_timestamp() where id='" + str(id) + "'"
                var.execute(query)
                text = """
%s %s (ip:%s) status 2 in host: %s
""" % ( name, type, multicast,ip)
                query="insert into logs (host, tag, datetime, msg) values ('" + protocol+"://"+multicast + "', 'status' ,NOW(),'" + text + "')"
                session.commit()        
configfile='/monitor/config.py'
if os.path.exists(configfile):
	execfile(configfile)
else:
	print "can't read file config";
	exit(1)
session=connect_mysql_db(host,port,user,password,db);
cur=session.cursor();
query="select pa.id,p.ip,p.protocol,pa.status,a.thread,c.name,p.type,pa.video from profile as p, agent as a, profile_agent as pa,channel as c where pa.profile_id=p.id and pa.agent_id=a.id and a.active=1 and pa.monitor=1 and pa.status=1 and p.channel_id=c.id and a.ip='" + ip +"'"
cur.execute(query);
rows = cur.fetchall();
for row in rows:
	while threading.activeCount() > 4:
		time.sleep(1);
	mysql=connect_mysql_db(host,port,user,password,db);
	t = threading.Thread(target=check_probe, args=(row[2],row[1],mysql,row[3],row[0],row[5],row[6],ip,row[7],));
	t.start();
time.sleep(75);
