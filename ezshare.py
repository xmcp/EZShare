#coding=utf-8

import cherrypy
from mako.template import Template
import os
import io
import mimetypes

from persistent import Database, File

DOWNLOAD_CHUNK=8*1024*1024
PASSWORD=os.environ.get('EZSHARE_AUTH')

def set_content_type():
    header=(b'Content-Type',cherrypy.response._content_type.encode())
    
    for ind,(key,_) in enumerate(cherrypy.response.header_list):
        if key.lower()==b'content-type':
            cherrypy.response.header_list[ind]=header
            break
    else:
        cherrypy.response.header_list.append(header)
        
cherrypy.tools.set_content_type=cherrypy.Tool('on_end_resource',set_content_type)

def _proc_mimetype(fn,charset):
    typ,_=mimetypes.guess_type(fn,False)
    if typ is None and not charset:
        return 'application/octet-stream'
    else:
        if typ is None or typ.startswith('text/'): #anti-xss
            typ='text/plain'
        return '%s; charset=%s'%(typ,charset) if charset else typ

def extract_visitor():
    orig_ip=cherrypy.request.remote.ip
    return ('IP: %s\nUA: %s\nLang: %s\nReferer: %s'%(
        cherrypy.request.headers['X-Real-IP'] if orig_ip=='127.0.0.1' and 'X-Real-IP' in cherrypy.request.headers else orig_ip,
        cherrypy.request.headers.get('User-Agent'),
        cherrypy.request.headers.get('Accept-Language'),
        cherrypy.request.headers.get('Referer'),
    )).split('\n')

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
                    'uploader': file.uploader,
                }

        return Template(filename='template.html',input_encoding='utf-8',output_encoding='utf-8').render(
            files=list(_getfiles()),
            persistent=bool(self.DB.connect_param),
            authed=PASSWORD is None or 'auth' in cherrypy.session
        )

    @cherrypy.expose()
    def auth(self,password):
        if PASSWORD is None or password==PASSWORD:
            cherrypy.session['auth']=True
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    @cherrypy.tools.set_content_type()
    def download(self,fileid,_=None,force_download=False):
        cherrypy.response._content_type='text/html'
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
                if force_download:
                    cherrypy.response._content_type='application/x-download'
                else:
                    cherrypy.response._content_type=_proc_mimetype(file.filename,file.charset)
                return stream()
        else:
            raise cherrypy.NotFound()

    @cherrypy.expose()
    def upload(self,upfile,filename=None):
        newfile=File(
            filename=filename or upfile.filename,
            content=upfile.file.read(),
            uploader=extract_visitor(),
        )
        self.FS[newfile.uuid]=newfile
        return 'OK'

    @cherrypy.expose()
    def uptext(self,content,captcha,filename=None):
        if captcha!=r'\\\\':
            raise cherrypy.HTTPRedirect('/')
        newfile=File(
            filename=filename or 'Document.txt',
            content=content.encode('utf-8'),
            uploader=extract_visitor(),
        )
        self.FS[newfile.uuid]=newfile
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def delete(self,fileid=None):
        if fileid and fileid in self.FS and not self.FS[fileid].persistent:
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
    def rename(self,fileid,filename):
        file=self.FS.get(fileid)
        if file:
            if file.persistent:
                if PASSWORD is not None and 'auth' not in cherrypy.session:
                    raise cherrypy.NotFound()
                self.DB.rename(file,filename)
            else:
                file.filename=filename
            raise cherrypy.HTTPRedirect('/')
        else:
            raise cherrypy.NotFound()

    @cherrypy.expose()
    def sync(self):
        self.DB.sync()
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose()
    def persistent(self,fileid):
        if PASSWORD is not None and 'auth' not in cherrypy.session:
            raise cherrypy.NotFound()
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
        'server.socket_host':'0.0.0.0',
        'server.socket_port':int(os.environ.get('PORT',os.environ.get('EZSHARE_PORT',80))),
        'server.max_request_body_size': 0, #no limit
    },
    '/': {
        'tools.gzip.on': True,
        'tools.response_headers.on':True,
        'tools.sessions.on': True,
        'tools.sessions.locking':'explicit',
    },
    '/static': {
        'tools.staticdir.on':True,
        'tools.staticdir.dir':os.path.join(os.getcwd(),'static'),
        'tools.response_headers.headers': [
            ('Cache-Control','max-age=86400'),
        ],
    },
    '/robots.txt': {
        'tools.staticfile.on':True,
        'tools.staticfile.filename':os.path.join(os.getcwd(),'static/robots.txt'),
    },
    '/download': {
        'tools.gzip.on': False, # it breaks content-length
        'response.stream': True,
    }
})
