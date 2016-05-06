#coding=utf-8
import os

import cherrypy
from mako.template import Template
import uuid
import time

class File:
    def __init__(self,filename,content):
        self.size=len(content)
        self.filename=filename
        self.uuid=uuid.uuid4().hex
        self.time=time.time()
        self.content=content
        try:
            self.content.decode('utf-8')
        except UnicodeDecodeError:
            self.istext=False
        else:
            self.istext=True


class Website:
    FS={}

    @cherrypy.expose()
    def index(self):
        def _getfiles():
            ret=[]
            for file in sorted(self.FS.values(),key=lambda x:-x.time):
                ret.append({
                    'filename': file.filename,
                    'size': file.size,
                    'uuid': file.uuid,
                    'time': file.time,
                    'istext': file.istext,
                })
            return ret

        return Template(filename='template.html',input_encoding='utf-8',output_encoding='utf-8')\
            .render(files=_getfiles())

    @cherrypy.expose()
    def download(self,fileid,force_download=None):
        if fileid in self.FS:
            file=self.FS[fileid]
            if file.istext and not force_download:
                cherrypy.response.headers['Content-Type']='text/plain'
            else:
                cherrypy.response.headers['Content-Type']='application/x-download'
                cherrypy.response.headers['Content-Disposition']='attachment; filename="%s"'%file.filename
            return file.content
        else:
            raise cherrypy.NotFound()

    @cherrypy.expose()
    def upload(self,upfile,filename=None):
        newfile=File(
            filename=filename or upfile.filename,
            content=upfile.file.read(),
        )
        self.FS[newfile.uuid]=newfile
        return 'OK'

    @cherrypy.expose()
    def uptext(self,content):
        newfile=File(
            filename='EZShare-Document.txt',
            content=content.encode('utf-8'),
        )
        self.FS[newfile.uuid]=newfile
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def delete(self,fileid):
        if fileid in self.FS:
            del self.FS[fileid]
            raise cherrypy.HTTPRedirect('/')
        else:
            raise cherrypy.NotFound()


cherrypy.quickstart(Website(),'/',{
    'global': {
        'engine.autoreload.on':False,
        # 'request.show_tracebacks': False,
        'server.socket_host':'0.0.0.0',
        'server.socket_port':80,
        'server.thread_pool':10,
    },
    '/': {
        'tools.gzip.on': True,
    },
    '/static': {
        'tools.staticdir.on':True,
        'tools.staticdir.dir':os.path.join(os.getcwd(),'static'),
    },
})