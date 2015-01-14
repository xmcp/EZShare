#coding=utf-8
import os
vp='%s/views/'%os.getcwd().replace('\\','/')
SAFETIME=600
MAXSIZE=50*1024*1024

import cherrypy
from mako.template import Template
import time

def err(s):
    return Template(filename=vp+'err.html',input_encoding='utf-8').render(err=s)

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
            timein=timein[-1]
        return int(timein.strip())*60


class File:
    def __init__(self,avid,filename,content,dietime):
        self.avid=avid
        self.filename=filename
        self.content=content
        self.dietime=dietime

class EZshare:
    datas=[File(filename='Welcome_to_EZShare.txt',avid='Hello',content=b'Hello World!',dietime=int(time.time())+3600)]

    def _refresh(self):
        for ind,data in enumerate(self.datas):
            if data.dietime<time.time():
                del self.datas[ind]
        if len(self.datas)>10:
            del self.datas[:len(self.datas)-10]

    @cherrypy.expose()
    def index(self):
        self._refresh()
        return Template(filename=vp+'index.html',input_encoding='utf-8').render(datas=self.datas,safetime=SAFETIME)

    @cherrypy.expose()
    def up(self,avid=None,file=None,upfile=None,uptext=None,strtime=None):
        if file is None or avid is None or strtime is None:
            return Template(filename=vp+'up.html',input_encoding='utf-8').render()
        dietime=int(time.time())+proctime(strtime)
        if dietime-time.time()>(24*60*60):
            return err('Time Too Long.')
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
        self.datas.append(File(avid=avid,filename=filename,content=content,dietime=dietime))
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def renew(self,avid):
        for data in self.datas:
            if data.avid==avid:
                if data.dietime<time.time()+SAFETIME:
                    data.dietime=time.time()+900
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def s(self,wd,view=False):
        for data in self.datas:
            if data.avid==wd:
                if view:
                    cherrypy.response.headers['Content-Type']='text/plain'
                else:
                    cherrypy.response.headers['Content-Type']='application/x-download'
                    cherrypy.response.headers['Content-Disposition']='attachment; filename="%s"'%data.filename
                return data.content
        return err('Cannot find file.')


cherrypy.config.update({'engine.autoreload.on':False})
cherrypy.quickstart(EZshare(),'')