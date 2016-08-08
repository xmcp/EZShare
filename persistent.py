#coding=utf-8

import os
from contextlib import closing
import psycopg2
import urllib.parse
import uuid
import datetime, pytz

urllib.parse.uses_netloc.append('postgres')

class File:
    def __init__(self,filename,content,uuid_=None,time_=None,persistent=False):
        self.size=len(content)
        self.filename=filename
        self.uuid=uuid_ or uuid.uuid4().hex
        self.time=time_ or datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai'))
        self.content=content
        self.persistent=persistent

class Database:
    def __init__(self,fs):
        url=urllib.parse.urlparse(os.environ.get('DATABASE_URL','postgres://localhost/'))
        self.connect_param=dict(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        self._cache={}
        self._fs=fs

    def _getdb(self):
        return psycopg2.connect(**self.connect_param)

    def _download(self,db,files):
        if not files:
            return
        cur=db.cursor()
        cur.execute('select id,content from storage where id in %s',[tuple(files)])
        for uuid_,content in cur.fetchall():
            self._cache[uuid.UUID(uuid_).hex]=bytes(content)

    def _sync(self, db):
        cur=db.cursor()
        cur.execute('select id,filename,upload_time from storage')
        items=cur.fetchall()
        self._download(db,[x[0] for x in items if x[0] not in self._cache])
        for file in self._fs.values(): #refresh persistent status
            file.persistent=False
        for uuid_,fn,time in items:
            uuid_=uuid.UUID(uuid_).hex
            self._fs[uuid_]=File(fn,self._cache.get(uuid_,'PERSISTENT ITEM NOT FOUND.'),uuid_,time,True)

    def upload(self,file:File):
        with self._getdb() as db:
            cur=db.cursor()
            cur.execute(
                'insert into storage (filename, id, upload_time, content) values (%s,%s,%s,%s)',
                [file.filename,file.uuid,file.time,file.content]
            )
            self._cache[file.uuid]=file.content
            self._sync(db)

    def remove(self,file:File):
        with self._getdb() as db:
            cur=db.cursor()
            cur.execute('delete from storage where id=%s',[file.uuid])
            file.persistent=False
            return cur.rowcount>0

    def sync(self):
        with self._getdb() as db:
            self._sync(db)