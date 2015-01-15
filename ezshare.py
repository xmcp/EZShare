#coding=utf-8
import os
vp='%s/views/'%os.getcwd().replace('\\','/')
SAFETIME=600
MAXSIZE=50*1024*1024
MAXALLSIZE=250*1024*1024
MAXLEN=10

import cherrypy
from mako.template import Template
import time

def err(s):
    return Template(filename=vp+'err.html',input_encoding='utf-8').render(err=str(s))

def proctime(timein):
    if ':' in timein: # xx : yy
        h,_,m=timein.partition(':')
        h,m=int(h),int(m)
        return h*3600+m*60
    elif 'h' in timein:
        h,_,m=timein.partition('h')
        h=int(h.strip())
        if m: # xx h yy m
            if m[-1]=='m':
                m=m[:-1]
            m=int(m.strip())
        else: # xx h
            m=0
        return h*3600+m*60
    else: # yy
        if timein[-1]=='m':
            timein=timein[:-1]
        return int(timein.rstrip())*60

class FS:
    files=[]
    size=0

    def addfile(self,avid,filename,content,dietime,istext):
        for file in self.files:
            if file.avid==avid:
                raise RuntimeError('AVID Exist.')
        if len(self.files)==MAXLEN:
            del self.files[0]
        self.files.append(File(avid,filename,content,dietime,istext))
        self.size+=len(content)

    def rmfile(self,avid):
        for ind,file in enumerate(self.files):
            if file.avid==avid:
                self.size-=len(file.content)
                del self.files[ind]
                return

    def getfile(self,avid):
        for file in self.files:
            if file.avid==avid:
                return file
        return False

    def __len__(self):
        return len(self.files)

class File:
    def __init__(self,avid,filename,content,dietime,istext):
        self.avid=avid
        self.filename=filename
        self.content=content
        self.dietime=dietime
        self.istext=istext

    def __bool__(self):
        return True

class EZshare:
    datas=FS()
    #datas.addfile(filename='Welcome to EZShare.txt',avid='Hello-World',content=b'Hello World!',dietime=int(time.time())+60,istext=False)

    def _refresh(self):
        for file in self.datas.files:
            if file.dietime<time.time():
                self.datas.rmfile(file.avid)

    @cherrypy.expose()
    def index(self):
        self._refresh()
        t=Template(filename=vp+'index.html',input_encoding='utf-8')
        return t.render(datas=self.datas.files,safetime=SAFETIME,maxlen=MAXLEN,maxallsize=MAXALLSIZE,size=self.datas.size)

    @cherrypy.expose()
    def up(self,avid=None,file=None,upfile=None,uptext=None,strtime=None):
        if file is None or avid is None or strtime is None:
            return Template(filename=vp+'up.html',input_encoding='utf-8').render()
        try:
            dietime=int(time.time())+proctime(strtime)
        except Exception as e:
            return err('时间无效: %s'%e)
        if self.datas.getfile(avid):
            return err('AVID Exist.')
        if dietime-time.time()>(24*60*60):
            return err('Time Too Long.')
        if not avid.replace('_','').replace('-','').isalnum():
            return err('Invalid AVID.')
        if file=='yes':
            filename=upfile.filename
            content=upfile.file.read()
        elif file=='no':
            filename='%s.txt'%avid
            content=uptext.encode()
        else:
            return err('Invalid File Parameter.')
        if len(content)>MAXSIZE:
            return err('File too big.')
        try:
            assert(content.decode().isprintable())
        except: #bin file
            istext=False
        else:
            istext=True
        self.datas.addfile(avid=avid,filename=filename,content=content,dietime=dietime,istext=istext)
        self._refresh()
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def renew(self,avid):
        item=self.datas.getfile(avid)
        if item:
            if item.dietime<time.time()+SAFETIME:
                item.dietime+=900
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def s(self,wd,mode='down'):
        data=self.datas.getfile(wd)
        if data:
            if mode=='text':
                if data.istext: #text file
                    cherrypy.response.headers['Content-Type']='text/plain'
                    return data.content
                else: #binary file
                    return Template(filename=vp+'binconfirm.html',input_encoding='utf-8').render(avid=wd)
            elif mode=='down':
                cherrypy.response.headers['Content-Type']='application/x-download'
                cherrypy.response.headers['Content-Disposition']='attachment; filename="%s"'%data.filename
                return data.content
            elif mode=='raw':
                del cherrypy.response.headers['Content-Type']
                return data.content
        else:
            return err('Cannot find file.')

cherrypy.config.update({
    'engine.autoreload.on':False,
    'server.socket_host':'0.0.0.0',
    'server.socket_port':7676,
})
cherrypy.quickstart(EZshare(),'')