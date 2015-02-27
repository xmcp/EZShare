#coding=utf-8
import os
vp='%s/views/'%os.getcwd().replace('\\','/')
SAFETIME=30*60
RENEWTIME=30*60
MAXSIZE=50*1024*1024
MAXALLSIZE=250*1024*1024
MAXLEN=20

import cherrypy
from mako.template import Template
import time

def err(s):
    return Template(filename=vp+'err.mako',input_encoding='utf-8').render(err=str(s))

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
    _FID=0

    def addfile(self,avid,filename,content,dietime,istext):
        for file in self.files:
            if file.avid==avid:
                raise RuntimeError('AVID Exist.')
        if len(self.files)==MAXLEN:
            self.size-=len(self.files[0].content)
            del self.files[0]
        while self.size>MAXALLSIZE:
            self.size-=len(self.files[0].content)
            del self.files[0]
        self.files.append(File(avid,filename,content,dietime,istext,fid=self._FID))
        self.size+=len(content)
        cherrypy.session['control'].append(self._FID)
        self._FID+=1

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
    def __init__(self,avid,filename,content,dietime,istext,fid):
        self.avid=avid
        self.filename=filename
        self.content=content
        self.dietime=dietime
        self.istext=istext
        self.fid=fid

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
        if 'control' not in cherrypy.session:
            cherrypy.session['control']=[]
        t=Template(filename=vp+'index.mako',input_encoding='utf-8')
        return t.render(datas=self.datas.files,safetime=SAFETIME,maxlen=MAXLEN,maxallsize=MAXALLSIZE,
                        size=self.datas.size,control=cherrypy.session['control'])

    @cherrypy.expose()
    def up(self,avid=None,file=None,upfile=None,uptext=None,strtime=None,xhr=None):
        if file is None or avid is None or strtime is None:
            return Template(filename=vp+'up.mako',input_encoding='utf-8').render()
        if 'control' not in cherrypy.session:
            cherrypy.session['control']=[]
        try:
            dietime=int(time.time())+proctime(strtime)
        except Exception as e:
            return err('Invalid Time: %s'%e)
        if self.datas.getfile(avid):
            return err('AVID Exist.')
        if dietime-time.time()>(24*60*60):
            return err('Time Too Long.')
        if not avid.replace('_','').replace('-','').isalnum():
            return err('Invalid AVID.')
        if file=='yes':
            try:
                filename=upfile.filename
                content=upfile.file.read()
            except Exception as e:
                return err('Cannot Upload File: %s'%e)
        elif file=='no':
            filename='%s.txt'%avid
            content=uptext.encode()
        else:
            return err('Invalid File Parameter.')
        if len(content)>MAXSIZE:
            return err('File too big.')
        try:
            content.decode()
        except: #bin file
            istext=False
        else:
            istext=True
        self._refresh()
        self.datas.addfile(avid=avid,filename=filename,content=content,dietime=dietime,istext=istext)
        if xhr:
            return 'OK'
        else:
            raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def renew(self,avid):
        item=self.datas.getfile(avid)
        if item:
            if item.dietime<time.time()+SAFETIME:
                item.dietime+=RENEWTIME
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def s(self,wd,mode='down'):
        self._refresh()
        data=self.datas.getfile(wd)
        if data:
            if mode=='text':
                if data.istext: #text file
                    cherrypy.response.headers['Content-Type']='text/plain'
                    return data.content
                else: #binary file
                    return Template(filename=vp+'binconfirm.mako',input_encoding='utf-8').render(avid=wd)
            elif mode=='down':
                cherrypy.response.headers['Content-Type']='application/x-download'
                cherrypy.response.headers['Content-Disposition']='attachment; filename="%s"'%data.filename
                return data.content
            elif mode=='raw':
                del cherrypy.response.headers['Content-Type']
                return data.content
        else:
            return err('Cannot find file.')

    @cherrypy.expose()
    def delete(self,avid):
        file=self.datas.getfile(avid)
        if not file:
            return err('No Such File.')
        if 'control' not in cherrypy.session or file.fid not in cherrypy.session['control']:
            return err('It\'s not Your File.')
        self.datas.rmfile(avid)
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def admin(self,avid=None):
        if 'control' not in cherrypy.session:
            cherrypy.session['control']=[]
        if avid:
            cherrypy.session['control'].append(self.datas.getfile(avid).fid)
        else:
            cherrypy.session['control']=[a.fid for a in self.datas.files]
        raise cherrypy.HTTPRedirect('/')

cherrypy.quickstart(EZshare(),'',{
    'global': {
         'engine.autoreload.on':False,
        'server.socket_host':'0.0.0.0',
        'server.socket_port':7676,
    },
    '/': {
        'tools.sessions.on':True,
    },
})