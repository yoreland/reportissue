import GithubManager
import json
import requests

headers = {'Content-Type': 'application/json'}


def send_wechat(content):
    datas = "## Github issue daily report:\n"
    datas += content
    datajson = {
        "msgtype": "markdown",
        "markdown": {
            "content": datas
        }
    }
    request_string = json.dumps(datajson)
    # print(request_string)
    # r = requests.post("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=90329971-0f13-469f-80ef-49901c457f70"
    #                   , data=request_string, headers=headers)
    # print(r.text)


def test_notify():
    content = GithubManager.repo_report()
    datajson = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    request_string = json.dumps(datajson)
    # print(request_string)
    r = requests.post("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=a4defae9-7d77-4071-80ca-1e6cc0a132cc"
                      , data=request_string, headers=headers)
    print(r.text)


if __name__ == "__main__":
    # send_wechat(GithubManager.generate_markdown_report())
    test_notify()
