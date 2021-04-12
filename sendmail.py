import emails
import GithubManager
from emails.template import JinjaTemplate as T
import yaml
import os
import json
import requests
headers = {'Content-Type': 'application/json'}

conf = None
with open(os.path.dirname(os.path.realpath(__file__)) + '/github.cfg') as f:
    conf = yaml.load(f, Loader=yaml.FullLoader)


smtp_conf = {'host': 'smtp.office365.com',
             'user': conf['USERNAME'],
             'password': conf['PASSWORD'],
             'port': 587,
             'tls': True}

#
def send_email(emailhtml):
    print(emailhtml)
    message = emails.html(subject=T('[Auto Notification]开源社区每日问题更新'),
                          html=T(emailhtml),
                          mail_from=('auto-reporter', conf['USERNAME']))
    r = message.send(to=conf['TO'], mail_from=conf['USERNAME'], smtp=smtp_conf)
    print(r)


def send_wechat(markdownStr):
    datas = "Github issue dialy report:\n> New Issues:8\n\n> Unhandled Issues:8\n\n| Repository  | Title  | Created Time  |\n|:----------|:----------|:----------|\n| AgoraIO/Agora-Flutter-SDK    | [SDK的example在iphone 8p上跑起来，占用存储空间有334MB](https://github.com/AgoraIO/Agora-Flutter-SDK/issues/286) | 2021-03-28 13\:02\:00    |"
    datajson = {
        "msgtype": "markdown",
        "markdown": {
            "content": datas
        }
    }
    requestStr = json.dumps(datajson)
    print(requestStr)
    r = requests.post("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ed05a5c1-3043-4107-89cd-5a412a197428", data=requestStr, headers=headers)
    print(r.text)


def generate_bug_report():
    html = "<h3>一年内标记为bug或enhancement的问题</h3>"
    html += append_header("label")
    html += GithubManager.generate_summary(GithubManager.sort_issue(GithubManager.bug_summary), "label")
    html += "</table>"
    return html


def generate_weekly_report():
    html = "<h3>两周内更新的问题</h3>"
    html += append_header("state")
    html += GithubManager.generate_summary(GithubManager.sort_issue(GithubManager.summary), "state")
    html += "</table>"
    return html


def append_header(state):
    header = "<table style='color:black;border:0;background-color: rgb(204, 204, " \
             "204);width=500px;line-height:20px' cellspacing='1' cellpadding='4'><tr " \
             "style='color:white;background-color:#1194ff;font-weight:900'><th>Repository</th>"
    header += "<th>" + state + "</th>"
    header += "<th>reporter</th>" \
              "<th>create time</th>" \
              "<th>last update</th>" \
              "<th>last modifier</th>" \
              "<th>title</th>" \
              "<th>description</th>" \
              "</tr>"
    return header


def generate_table_row(item, state):
    row_str = "<tr>"
    row_str += "<td bgcolor='white'>" + item.repo + "</td>"
    if state == "state":
        cur_status = item.state
        if cur_status == "closed":
            row_str += "<td style='color:white;background-color:rgb(0, 145, 226)'>" + item.state + "</td>"
        else:
            row_str += "<td style='color:white;background-color:rgb(226, 211, 0)'>" + item.state + "</td>"
    else:
        if GithubManager.check_tag(item):
            row_str += "<td style='color:white;background-color:rgb(0, 145, 226)'>enhancement</td>"
        else:
            row_str += "<td style='color:white;background-color:rgb(226, 211, 0)'>bug</td>"
    row_str += "<td bgcolor='white'>" + item.user.login + "</td>"
    row_str += "<td bgcolor='white'>" + str(item.created_at) + "</td>"
    row_str += "<td bgcolor='white'>" + item.updated_category + "</td>"
    row_str += "<td bgcolor='white'>" + str(item.owner) + "</td>"
    row_str += "<td bgcolor='white'><a href=" + item.html_url + ">" + item.title + "</a></td>"
    description = item.body
    if len(item.body) > 180:
        description = item.body[0:180]
    row_str += "<td bgcolor='white'>" + description + "</td>"
    row_str += "</tr>"
    return row_str


if __name__ == "__main__":
#     send_email(GithubManager.getHtmlSummary())
    send_wechat("")
