import emails
from datetime import datetime, timedelta
import github
import yaml
import logging
import os

from emails.template import JinjaTemplate as T

log = logging.getLogger(__name__)
conf = None
with open(os.path.dirname(os.path.realpath(__file__)) + '/github.cfg') as f:
    conf = yaml.load(f, Loader=yaml.FullLoader)
log.info("Config loaded")
github_client = github.Github(
    conf['api_token'],
    user_agent='agent')
summary = []
bug_summary = []
repos = []
table_rows = []
email_html = ""
issue_closed_count = 0
issue_created_count = 0
issue_replied_count = 0

class RepoIssues:
    def __init__(self, name, count):
        self.name = name
        self.count = count


def filter_labels(res2):
    res = []
    for item in res2:
        for label in item.labels:
            if label.name == 'bug' or label.name == 'enhancement':
                res.append(item)
                break
    return res


def fetch_issues_by_repo(repo_name):
    repo = github_client.get_repo(repo_name.full_name)
    two_week_before = datetime.today() + timedelta(days=-14)
    one_year_before = datetime.today() + timedelta(days=-365)
    res1 = repo.get_issues(state='all', since=two_week_before, sort='updated', direction='desc')
    res2 = repo.get_issues(since=one_year_before, sort='updated', direction='desc')
    for item in res1:
        item.repo = repo.full_name
    for item in res2:
        item.repo = repo.full_name
    summary.append(res1)
    bug_summary.append(filter_labels(res2))


def fetch_issues_by_repo_old(repo):
    week_before = datetime.today() + timedelta(days=-14)
    res = repo.get_issues(state='all', since=week_before, sort='updated', direction='desc')
    for item in res:
        item.repo = repo.full_name
    return res


def fetch_issues_by_repo_need_reply(repo):
    three_month_before = datetime.today() + timedelta(weeks=-12)
    res = repo.get_issues(state='all', since=three_month_before, sort='updated', direction='desc')
    for item in res:
        item.repo = repo.full_name
    return res


def count_replied_issues_by_repo(repo):
    global issue_replied_count
    three_month_before = datetime.today() + timedelta(weeks=-12)
    issues = repo.get_issues(state='all', since=three_month_before)
    need_print = 0
    count = 0
    for issue in issues:
        if not issue.pull_request and issue.created_at.month > 6:
            need_print = 1
            for comment in issue.get_comments():
                count += 1
                break
    if need_print > 0:
        issue_replied_count += count
        print(repo.full_name + "," + str(count))


def count_close_issues_by_repo(repo):
    global issue_closed_count, issue_created_count, issue_replied_count
    three_month_before = datetime.today() + timedelta(days=-7)
    issues = repo.get_issues(state='closed', since=three_month_before)
    issues_new = repo.get_issues(state='all', since=three_month_before)
    count = 0
    for issue in issues:
        if not issue.pull_request and issue.created_at.month > 6:
            for comment in issue.get_comments():
                count += 1
                break
    if count > 0:
        issue_closed_count += count
    count_new = 0
    count_reply = 0
    for issue in issues_new:
        if not issue.pull_request and issue.created_at.month > 6:
            if issue.state != "closed":
                count_new += 1
            for comment in issue.get_comments():
                count_reply += 1
                if issue.state == "closed":
                    count_new += 1
                break
    issue_created_count += count_new
    issue_replied_count += count_reply
    if count > 0 or count_new > 0 or count_reply > 0:
        print(repo.full_name + "," + str(count) + "," + str(count_new) + "," + str(count_reply))


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


def generate_summary(summaries, state):
    table_body = ""
    if os.path.exists('./daily.csv'):
        os.remove('./daily.csv')
    try:
        for item in summaries:
            table_body += generate_table_row(item, state)
        return table_body
    except Exception:
        log.error("Failed to write summary")
        return ""


def check_tag(item):
    for label in item.labels:
        if label.name == 'enhancement':
            return True
    return False


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
        if check_tag(item):
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


def send_email(emailhtml):
    message = emails.html(subject=T('[Auto Notification]开源社区每日问题更新'),
                          html=T(emailhtml),
                          mail_from=('auto-reporter', conf['USERNAME']))
    r = message.send(to=conf['TO'], mail_from=conf['USERNAME'], smtp=smtp_conf)
    print(r)


def generate_bug_report():
    html = "<h3>一年内标记为bug或enhancement的问题</h3>"
    html += append_header("label")
    html += generate_summary(sort_issue(bug_summary), "label")
    html += "</table>"
    return html


def generate_weekly_report():
    html = "<h3>两周内更新的问题</h3>"
    html += append_header("state")
    html += generate_summary(sort_issue(summary), "state")
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


smtp_conf = {'host': 'smtp.office365.com',
             'user': conf['USERNAME'],
             'password': conf['PASSWORD'],
             'port': 587,
             'tls': True}


def printsum():
    if 'repositories' in conf:
        for org_details in conf['orgs']:
            org = github_client.get_organization(org_details['org'])
            for repo in org.get_repos():
                count_close_issues_by_repo(repo)
        print("total," + str(issue_closed_count) + "," + str(issue_created_count) + "," + str(issue_replied_count))


def printsum1():
    if 'repositories' in conf:
        for org_details in conf['orgs']:
            org = github_client.get_organization(org_details['org'])
            for repo in org.get_repos():
                count_replied_issues_by_repo(repo)
        print("total," + str(issue_replied_count))


def getHtmlSummary():
    global email_html
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
                fetch_issues_by_repo(repo)
                # items = fetch_issues_by_repo_need_reply(repo)
                # summary.append(items)
        # email_html += generate_summary(sort_issue(summary))
        email_html += generate_weekly_report()
        email_html += generate_bug_report()
        return email_html

if __name__ == "__main__":
    send_email(getHtmlSummary())
    # printsum()
