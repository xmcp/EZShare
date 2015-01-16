<!DOCTYPE html>
<% import time %>
<html>
<head lang="zh">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <link href="http://libs.useso.com/js/bootstrap/3.2.0/css/bootstrap.min.css" rel="stylesheet">
    <script src="http://libs.useso.com/js/jquery/2.1.1/jquery.min.js"></script>
    <script src="http://libs.useso.com/js/bootstrap/3.2.0/js/bootstrap.min.js"></script>
    <!--[if lt IE 9]>
        <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
        <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
    <title>EZShare</title>
    <script>
        function look(avid,fname) {
            var timebtn=$('#look-modal-timebtn');
            $('#look-modal-avid').html(avid);
            $('#look-modal-title').html(fname);
            $('#look-modal-body').attr('src','/s?mode=text&wd='+avid);
            $('#look-modal-time').html($('#timebar-'+avid).html());
            if($('#timebtn-'+avid).attr('disabled')) {
                timebtn.attr('disabled', 'disabled');
                timebtn.removeClass('btn-warning').addClass('btn-default');
            }
            else {
                timebtn.removeAttr('disabled');
                timebtn.addClass('btn-warning').removeClass('btn-default');
            }
            $('#look-modal').modal('show');
        }
        function down(avid) {
            window.open('/s?mode=down&wd='+avid)
        }
        function renew(avid) {
            window.location.assign('/renew?avid='+avid)
        }
        function del(avid) {
            if(confirm('确定要删除 '+avid+' 吗？'))
                window.location.assign('/delete?avid='+avid)
        }
        function renew_this() {renew($('#look-modal-avid').html());}
        function down_this() {down($('#look-modal-avid').html());}
    </script>
</head>
<body style="background-color: #DDD"><div class="container">
<nav class="navbar navbar-default">
    <div class="container-fluid">
        <div class="navbar-header" style="width: 100%">
            <a href="/up" class="btn btn-primary navbar-btn pull-right">
                <span class="glyphicon glyphicon-cloud-upload"></span>
            </a>
            <a class="navbar-brand" href="/">
                <span class="glyphicon glyphicon-share-alt"></span>
                &nbsp;EZShare
            </a>
        </div>
    </div>
</nav>
<ul class="list-group" style="width: 100%;">
    % for data in datas:
        <li class="list-group-item" style="line-height: 33px; min-height: 56px;">
            <div class="btn-group pull-right" role="group">
                % if data.fid in control:
                    <button type="button" class="btn btn-danger" onclick="del('${data.avid}')">
                        <span class="glyphicon glyphicon-trash"></span>
                        <span class="hidden-xs">&nbsp;删除</span>
                    </button>
                % endif
                <button type="button" class="btn btn-default" onclick="look('${data.avid}','${data.filename}')">
                    <span class="glyphicon glyphicon-eye-open"></span>
                    <span class="hidden-xs">&nbsp;查看</span>
                </button>
                <button type="button" class="btn btn-default" onclick="down('${data.avid}')">
                    <span class="glyphicon glyphicon-floppy-save"></span>
                    <span class="hidden-xs">&nbsp;下载</span>
                </button>
                <% timetogo=int(data.dietime-time.time()) %>
                % if timetogo<safetime:
                    <button type="button" onclick="renew('${data.avid}')" class="btn btn-warning" id="timebtn-${data.avid}">
                        <span class="glyphicon glyphicon-flash hidden-xs"></span>
                        <b id="timebar-${data.avid}">${timetogo//3600}:${'%02d'%(timetogo//60%60)}</b>
                    </button>
                % else:
                    <button type="button"  class="btn btn-default" disabled="disabled" id="timebtn-${data.avid}">
                        <span class="glyphicon glyphicon-flash hidden-xs"></span>
                        <b id="timebar-${data.avid}">${timetogo//3600}:${'%02d'%(timetogo//60%60)}</b>
                    </button>
                % endif
            </div>
            <a href="#" style="text-decoration: none" onclick="look('${data.avid}','${data.filename}')">
                <b>${data.avid}</b>&nbsp;
                <span class="label label-default">
                    <span class="glyphicon glyphicon-${'envelope' if data.istext else 'paperclip'}"></span>
                    ${data.filename}
                </span>
            </a>
        </li>
    % endfor
</ul>
<div style="padding-left: 5px; padding-right: 5px;">
    % if datas:
        <div class="row">
            <div class="col-sm-4">
                <div class="progress" style="margin-bottom: 0 !important;">
                    <div class="progress-bar ${'' if maxlen-len(datas)>1 else 'progress-bar-warning'}"
                         style="width: ${100*len(datas)/maxlen}%;"></div>
                </div>
                <p class="small" style="position: relative; top: -18px; left: 5px; text-align: center">
                    ${len(datas)} 个文件
                </p>
            </div>
            <div class="col-sm-4">
                <div class="progress" style="margin-bottom: 0 !important;">
                    <div class="progress-bar ${'' if maxallsize-size>50*1024*1024 else 'progress-bar-warning'}"
                         style="width: ${100*size/maxallsize}%;"></div>
                </div>
                <p class="small" style="position: relative; top: -18px; left: 5px; text-align: center">
                    共 ${'%.2f'%(size/1024/1024)} MB
                </p>
            </div>
            <div class="col-sm-4">
                <p class="small" style="text-align: center">空间满后，靠前的文件会被优先删除。</p>
            </div>
        </div>
    % else:
        <div class="alert alert-info">
            <span class="glyphicon glyphicon-inbox"></span>&nbsp;&nbsp;没有分享的文件
        </div>
    % endif
    <a class="pull-right" href="https://github.com/xmcp/ezshare" target="_blank">by xmcp</a>
</div>

<!-- look modal -->
<div class="modal fade" id="look-modal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
                <h4 class="modal-title">
                    <span id="look-modal-avid">NULL</span>:&nbsp;
                    <span id="look-modal-title">未选择文件</span>
                </h4>
            </div>
            <div class="modal-body" >
                <iframe style="width: 100%; height: 300px; border: 0px;" id="look-modal-body"></iframe>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" id="look-modal-timebtn"  onclick="renew_this()">
                    <span class="glyphicon glyphicon-flash"></span>
                    <b id="look-modal-time"></b>
                </button>
                <button type="button" class="btn btn-primary" onclick="down_this()">下载</button>
            </div>
        </div>
    </div>
</div>
</div></body>
</html>