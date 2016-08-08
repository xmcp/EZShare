#coding=utf-8

import cherrypy
from mako.template import Template

import os
import io

from persistent import Database, File

DOWNLOAD_CHUNK=8*1024*1024

class Website:
    def __init__(self):
        self.FS={}
        self.DB=Database(self.FS)

    @cherrypy.expose()
    def index(self):
        def _getfiles():
            for file in sorted(self.FS.values(),key=lambda x:x.time,reverse=True):
                yield {
                    'filename': file.filename,
                    'size': file.size,
                    'uuid': file.uuid,
                    'time': file.time,
                    'persistent': file.persistent,
                }

        return Template(filename='template.html',input_encoding='utf-8',output_encoding='utf-8')\
            .render(files=list(_getfiles()),persistent=bool(self.DB.connect_param))

    @cherrypy.expose()
    def download(self,fileid,_=None,force_download=False):
        def stream():
            data=obj.read(DOWNLOAD_CHUNK)
            while data:
                yield data
                data=obj.read(DOWNLOAD_CHUNK)
    
        if fileid in self.FS:
            file=self.FS[fileid]
            try:
                obj=io.BytesIO(file.content)
            except MemoryError:
                return '内存不足，文件无法下载'
            else:
                cherrypy.response.headers['Content-Length']=file.size
                cherrypy.response.headers['Content-Type']='application/x-download' if force_download else 'text/plain'
                return stream()
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
            filename='Document.txt',
            content=content.encode('utf-8'),
        )
        self.FS[newfile.uuid]=newfile
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def delete(self,fileid=None):
        if fileid and fileid in self.FS:
            del self.FS[fileid]
            raise cherrypy.HTTPRedirect('/')
        elif fileid is not None:
            raise cherrypy.NotFound()
        else:
            for fileid in list(self.FS):
                if not self.FS[fileid].persistent:
                    del self.FS[fileid]
            raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def sync(self):
        self.DB.sync()
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def persistent(self,fileid):
        file=self.FS.get(fileid)
        if file:
            if file.persistent:
                if not self.DB.remove(file):
                    raise cherrypy.NotFound()
            else:
                self.DB.upload(file)
            raise cherrypy.HTTPRedirect('/')
        else:
            raise cherrypy.NotFound()

cherrypy.quickstart(Website(),'/',{
    'global': {
        'engine.autoreload.on':False,
        # 'request.show_tracebacks': False,
        'server.socket_host':'0.0.0.0',
        'server.socket_port':int(os.environ.get('PORT',80)),
        'server.thread_pool':10,
        'server.max_request_body_size': 0, #no limit
    },
    '/': {
        'tools.gzip.on': True,
    },
    '/static': {
        'tools.staticdir.on':True,
        'tools.staticdir.dir':os.path.join(os.getcwd(),'static'),
        'tools.response_headers.headers': [
            ('Cache-Control','max-age=86400'),
        ],
    },
    '/download': {
        'response.stream': True,
    }
})