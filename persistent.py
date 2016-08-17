#coding=utf-8
"""
-- PostgreSQL DDL
CREATE TABLE storage (
   filename     text          NOT NULL,
   id           uuid          NOT NULL,
   upload_time  timestamptz   NOT NULL,
   content      bytea         NOT NULL
);
ALTER TABLE public.storage ADD CONSTRAINT storage_pkey PRIMARY KEY (id);
CREATE UNIQUE INDEX storage_id_uindex ON storage USING btree (id);
"""

import os
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
        self._cache={}
        self._fs=fs
        if 'DATABASE_URL' in os.environ:
            url=urllib.parse.urlparse(os.environ['DATABASE_URL'])
            self.connect_param=dict(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
            )
            print('=== Initializing persistent database...')
            self.sync()
            print('=== Done. %d objects fetched.'%len(self._fs))
        else:
            print('=== DATABASE_URL not set. Persistence mode disabled.')
            self.connect_param={}

    def _getdb(self):
        return psycopg2.connect(**self.connect_param)

    def _download(self,db,files):
        if not files:
            return
        print('=== Downloading %d untracked files...'%len(files))
        cur=db.cursor()
        cur.execute('select id,content from storage where id in %s',[tuple(files)])
        for uuid_,content in cur.fetchall():
            self._cache[uuid.UUID(uuid_).hex]=bytes(content)

    def _sync(self, db):
        cur=db.cursor()
        cur.execute('select id,filename,upload_time from storage')
        items=cur.fetchall()
        self._download(db,[uuid.UUID(x[0]).hex for x in items if uuid.UUID(x[0]).hex not in self._cache])
        for file in self._fs.values(): #refresh persistent status
            file.persistent=False
        for uuid_,fn,time in items:
            uuid_=uuid.UUID(uuid_).hex
            self._fs[uuid_]=File(
                fn,
                self._cache.get(uuid_,'PERSISTENT ITEM NOT FOUND.'),
                uuid_,
                time+datetime.timedelta(hours=8),
                True
            )

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