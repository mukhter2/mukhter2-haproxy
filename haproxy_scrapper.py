#from asyncio.windows_events import NULL
from unicodedata import name
from unittest import result
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import pandas as pd
from time import sleep, time
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import sys
import os
import sched, time
import datetime 
import re
import logging
from prettytable import PrettyTable
from selenium.common.exceptions import WebDriverException
import MySQLdb
thedict={}
indivServer={}
options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
s=Service(ChromeDriverManager().install())
driver = webdriver.Chrome(options=options, service=s)
driver.implicitly_wait(200)
import config
siteNames=config.total
print(siteNames)
startTime=datetime.datetime.now()
level = logging.INFO
format= ' %(message)s '
handlers = [logging.FileHandler('haproxy_status.log'), logging.StreamHandler()]
logging.basicConfig(level = level, format = format, handlers = handlers)
def hms(s):
    l = list(map(int, re.split('[hms]', s)[:-1]))
    if len(l) == 3:
        return l[0]*3600 + l[1]*60 + l[2]
    elif len(l) == 2:
        return l[0]*60 + l[1]
    else:
        return l[0]    
runMaxSes=0
runMaxTotSes=0  
runMaxNumbError=0   
runMaxFroSes=0  
runMaxFroTotSes=0    
runListServer={}
def infinite_loop(sc):
    global runMaxSes,runMaxTotSes,runMaxNumbError,runMaxFroSes,runMaxFroTotSes    
    connected=False
    while not connected:
        try:
            global driver
            driver.get(siteNames)        
            connected=True
        except WebDriverException as e:
            print(e.msg)
            connected=False
            pass        
    content=driver.page_source
    soup=BeautifulSoup(content,'html.parser')
    a=soup.find('h2').get_text().strip()
    a=a.replace('Statistics Report for pid ','')
    td_list =driver.find_elements(By.CLASS_NAME,value='backend')
    lipe= list(td_list[1].text.split(' '))
    td_list2 =driver.find_elements(By.CLASS_NAME,value='frontend')
    lipe2= list(td_list2[1].text.split())
    td_list3=driver.find_elements(By.CLASS_NAME, value='active_up')    
    for x in range(1,len(td_list3)):
        liper = td_list3[x].text.split()
        indivServer[(int(a),str(liper[0]))]=[int(liper[4]),int(liper[5]),int(liper[6]),int(liper[7]),int(liper[9]),int(liper[15])]
        runListServer[str(liper[0])]=[str(liper[0]),0,0,0,0,0,0]        
    # print(indivServer)
    #print(lipe2)
    timeSec=0
    try:
        timeSec= int(hms(lipe[16]))        
    except:
        timeSec=11
    if timeSec<10:
        thedict.clear()
        indivServer.clear()
    thedict[int(a)]=[int(lipe[3]),int(lipe[4]),int(lipe[5]),int(lipe[6]),int(lipe[13]),datetime.datetime.now(),int(lipe2[1]),int(lipe2[2]),int(lipe2[4]),int(lipe2[5])]
    #print(a,'',lipe[3],'',lipe[4],'',lipe[5],'',lipe[6])
    s.enter(5, 1, infinite_loop, (sc,))
    #print(thedict)
    sum1=0
    sum2=0
    sum3=0
    sum4=0
    sum2min1=0
    sum2min2=0
    cnt=0
    err=0
    frontSum1=0
    frontSum2=0
    frontSum3=0
    frontSum4=0
    hur=len(td_list3)-1
    serverList=[[]]*hur
    cnterX=0    
    for key in indivServer:
        runListServer[key[1]][1]+=indivServer[key][0]
        runListServer[key[1]][2]+=indivServer[key][1]
        runListServer[key[1]][3]+=indivServer[key][2]
        runListServer[key[1]][4]+=indivServer[key][3]
        runListServer[key[1]][5]+=indivServer[key][4]
        runListServer[key[1]][6]+=indivServer[key][5]        
    # print(serverList)
    for key in thedict:
        fd=thedict[key][0]
        fds=thedict[key][2]
        fda=thedict[key][1]
        fdsf=thedict[key][3]
        err+=thedict[key][4]
        frontSum1+=thedict[key][6]
        frontSum2+=thedict[key][7]
        frontSum3+=thedict[key][8]
        frontSum4+=thedict[key][9]
        sum1+=fd
        sum2+=fds
        sum3+=fda
        sum4+=fdsf
        runMaxSes=max(sum2,runMaxSes)
        runMaxTotSes=max(sum4,runMaxTotSes)
        runMaxNumbError=max(runMaxNumbError,err)
        runMaxFroSes=max(runMaxFroSes,frontSum3)
        runMaxFroTotSes=max(runMaxFroTotSes,frontSum4)
        timme= datetime.datetime.now()-thedict[key][5]
        totsec=timme.total_seconds()
        if totsec<120:
            sum2min1+=fd
            sum2min2+=fds
            cnt+=1
    stm=str(datetime.datetime.now())	
    sareadf=str(startTime)
    t = PrettyTable(['Name', 'current session rate','max session rate','current session','max session','total session','error'])
    for xer in runListServer:
        t.add_row(runListServer[xer])
        sqlqry='INSERT INTO HaProxy.all_server_monitor(server_name,cur_ses_rate,max_ses_rate,cur_ses,max_ses,tot_ses,error,init_time, nproc) VALUES (%s, %s, %s, %s, %s,%s, %s, %s, %s)'
        valr=(runListServer[xer][0],runListServer[xer][1],runListServer[xer][2],runListServer[xer][3],runListServer[xer][4],runListServer[xer][5],runListServer[xer][6],sareadf,len(thedict))
        db=MySQLdb.connect("localhost","root","abcd1234.","HaProxy")
        insertrec=db.cursor()
        insertrec.execute(sqlqry,valr)
        db.commit()
        db.close()
    print('server record saved')
    front_table = PrettyTable(['total process','total session rate', 'total session','total maximum session rate','total maximum session'])
    front_table.add_row([len(thedict),frontSum1,frontSum3,frontSum2,frontSum4])
    back_table = PrettyTable(['total process','total session rate', 'total session','total maximum session rate','total maximum session','total number of error'])
    back_table.add_row([len(thedict),sum1,sum2,sum3,sum4,err])
    sqlquery='INSERT INTO HaProxy.backend_info(Session_Rate, Session, Max_Session_Rate, Max_Session, Error) values (%s, %s, %s, %s, %s)'
    valr=(sum1,sum2,sum3,sum4,err)
    db=MySQLdb.connect("localhost","root","abcd1234.","HaProxy")
    insertrec=db.cursor()
    insertrec.execute(sqlquery,valr)
    db.commit()
    print('record saved')
    db.close()
    logging.info(f'---------start on {stm}---------\n')
    logging.info(f'Initial time: {sareadf}')
    mat=datetime.datetime.now()-startTime
    mats=int(mat.total_seconds())
    logging.info(f'Running for: {mats}')
    logging.info(f'total process: {len(thedict)}')
    logging.info('\n-----------------Frontend-----------------------\n')
    logging.info(front_table)
    logging.info('\n-----------------Backend------------------------\n')
    
    logging.info(back_table)
    logging.info('\n------------------backend filter------------------\n')

    back_table_filter = PrettyTable(['total process(2min)','total session rate(2min)', 'total session(2min)'])
    back_table_filter.add_row([cnt,sum2min1,sum2min2])
    logging.info(back_table_filter)
    
    logging.info('\n-----------------Overall Highest Values-------------------------\n')
    
    overall_table = PrettyTable(['session','Max session','error', 'Frontend session','Frontend Maximum session'])
    overall_table.add_row([runMaxSes,runMaxTotSes,runMaxNumbError,runMaxFroSes,runMaxFroTotSes])
    logging.info(overall_table)
    logging.info('\n-----------------All Server Monitor-------------------------\n')
    logging.info(f'total process: {len(thedict)}')
    logging.info(t)
    logging.info('\n-----------------------END--------------------------\n')

s = sched.scheduler(time.time, time.sleep)
s.enter(5, 1, infinite_loop, (s,))
s.run()
