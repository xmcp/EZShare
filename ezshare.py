#coding=utf-8
import os
vp='%s/views/'%os.getcwd().replace('\\','/')

import cherrypy
from mako.template import Template

def err(s):
    return Template(filename=vp+'err.html',input_encoding='utf-8').render(err=s)

class File:
    def __init__(self,avid,filename,content):
        self.avid=avid
        self.filename=filename
        self.content=content

class EZshare:
    datas=[File(filename='1.txt',avid='111',content=b'233')]

    @cherrypy.expose()
    def index(self):
        return Template(filename=vp+'index.html',input_encoding='utf-8').render(datas=self.datas)

    @cherrypy.expose()
    def up(self,avid=None,file=None,upfile=None,uptext=None):
        if file is None or avid is None:
            return Template(filename=vp+'up.html',input_encoding='utf-8').render()
        if file=='yes':
            self.datas.append(File(avid=avid,filename=upfile.filename,content=upfile.file.read()))
        elif file=='no':
            self.datas.append(File(avid=avid,filename='%s.txt'%avid,content=uptext))
        else:
            return err('Invalid File Parameter.')
        raise cherrypy.HTTPRedirect('/')


cherrypy.config.update({'engine.autoreload.on':False})
cherrypy.quickstart(EZshare(),'')