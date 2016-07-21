#coding=utf-8
import os

import cherrypy
from mako.template import Template
import uuid
import datetime, pytz

class File:
    def __init__(self,filename,content):
        self.size=len(content)
        self.filename=filename
        self.uuid=uuid.uuid4().hex
        self.time=datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai'))
        self.content=content


class Website:
    FS={}

    @cherrypy.expose()
    def index(self):
        def _getfiles():
            for file in sorted(self.FS.values(),key=lambda x:x.time,reverse=True):
                yield {
                    'filename': file.filename,
                    'size': file.size,
                    'uuid': file.uuid,
                    'time': file.time,
                }

        return Template(filename='template.html',input_encoding='utf-8',output_encoding='utf-8')\
            .render(files=list(_getfiles()))

    @cherrypy.expose()
    def download(self,fileid,_=None,force_download=False):
        if fileid in self.FS:
            file=self.FS[fileid]
            if force_download:
                cherrypy.response.headers['Content-Type']='application/x-download'
            else:
                cherrypy.response.headers['Content-Type']='text/plain'

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
            self.FS.clear()
            raise cherrypy.HTTPRedirect('/')


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
    },
})