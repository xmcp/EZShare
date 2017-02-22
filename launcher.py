import socket
print('Your IP address:  %s'%'  '.join(socket.gethostbyname_ex(socket.gethostname())[2]))
print('='*79)

print('== Loading modules...')
import ezshare
import sys
import os

print('== Uploading files...')
website=ezshare.Website()

def _walk(dn):
    if os.path.isfile(dn):
        yield dn
    else:
        for path,_dirs,files in os.walk(dn):
            for file in files:
                yield os.path.join(path,file)

for dn in sys.argv[1:]:
    for fn in _walk(dn):
        print(' ->',fn)
        with open(fn,'rb') as f:
            file=ezshare.File(
                filename=os.path.basename(fn),
                content=f.read(),
                uploader=[fn,'ezShare launcher'],
            )
            website.FS[file.uuid]=file
        
print('== Starting server...')
os.chdir(os.path.split(sys.argv[0])[0])
ezshare.run(website)