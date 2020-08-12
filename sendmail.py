import emails
from datetime import datetime, timedelta
import github
import yaml
import logging
import os

from emails.template import JinjaTemplate as T

log = logging.getLogger(__name__)
conf = None
with open('github.cfg') as f:
    conf = yaml.load(f, Loader=yaml.FullLoader)
log.info("Config loaded")
github_client = github.Github(
    conf['api_token'])
summary = []
repos = []
table_rows = []
email_html = ""


class RepoIssues:
    def __init__(self, name, count):
        self.name = name
        self.count = count


def fetch_issues_by_repo(repo):
    week_before = datetime.today() + timedelta(days=-14)
    res = repo.get_issues(state='all', since=week_before, sort='updated', direction='desc')
    for item in res:
        item.repo = repo.full_name
    return res


def sort_issue(repos_issues):
    res = []
    for repo in repos_issues:
        for item in repo:
            if item.pull_request is None:
                item.updated_category = pretty_date(item.updated_at)
                item.owner = ""
                if item.comments > 0:
                    item.owner = item.get_comments()[item.comments - 1].user.login
                res.append(item)
    return sorted(res, key=lambda issue_obj: (issue_obj.state, issue_obj.created_at.timestamp()), reverse=True)


def pretty_date(time=False):
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(int(second_diff)) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(int(second_diff / 60)) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(int(day_diff)) + " days ago"
    if day_diff < 31:
        return str(int(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(int(day_diff / 30)) + " months ago"
    return str(int(day_diff / 365)) + " years ago"


def generate_summary(summaries):
    table_body = ""
    if os.path.exists('./daily.csv'):
        os.remove('./daily.csv')
    try:
        for item in summaries:
            table_body += generate_table_row(item)
        return table_body
    except Exception:
        log.error("Failed to write summary")
        return ""


def generate_table_row(item):
    row_str = "<tr>"
    row_str += "<td bgcolor='white'>" + item.repo + "</td>"
    cur_status = item.state
    if cur_status == "closed":
        row_str += "<td style='color:white;background-color:rgb(0, 145, 226)'>" + item.state + "</td>"
    else:
        row_str += "<td style='color:white;background-color:rgb(226, 211, 0)'>" + item.state + "</td>"
    row_str += "<td bgcolor='white'>" + item.user.login + "</td>"
    row_str += "<td bgcolor='white'>" + str(item.created_at) + "</td>"
    row_str += "<td bgcolor='white'>" + item.updated_category + "</td>"
    row_str += "<td bgcolor='white'>" + str(item.owner) + "</td>"
    row_str += "<td bgcolor='white'><a href="+item.html_url+">" + item.title + "</a></td>"
    description = item.body
    if len(item.body) > 180:
        description = item.body[0:180]
    row_str += "<td bgcolor='white'>" + description + "</td>"
    row_str += "</tr>"
    return row_str


def send_email(emailhtml):
    message = emails.html(subject=T('[Auto Notification]开源社区每日问题更新'),
                          html=T(emailhtml),
                          mail_from=('auto-reporter', conf['USERNAME']))
    r = message.send(to=conf['TO'], mail_from=conf['USERNAME'], smtp=smtp_conf)
    print(r)


if 'repositories' in conf:
    email_html += "<table style='color:black;border:0;background-color: rgb(204, 204, 204);width=500px;line-height:20px' cellspacing='1' cellpadding='4'><tr style='color:white;background-color:#1194ff;font-weight:900'><th>Repository</th>" \
                  "<th>state</th>" \
                  "<th>reporter</th>" \
                  "<th>create time</th>" \
                  "<th>last update</th>" \
                  "<th>last modifier</th>" \
                  "<th>title</th>" \
                  "<th>description</th>" \
                  "</tr>"
    log.debug("Using configured repository list")
    for org_details in conf['orgs']:
        org = github_client.get_organization(org_details['org'])
        for repo in org.get_repos():
            items = fetch_issues_by_repo(repo)
            summary.append(items)
    email_html += generate_summary(sort_issue(summary))
email_html += "</table>"
smtp_conf = {'host': 'smtp.office365.com',
             'user': conf['USERNAME'],
             'password': conf['PASSWORD'],
             'port': 587,
             'tls': True}
if __name__ == "__main__":
    send_email(email_html)
