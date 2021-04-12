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
    r = requests.post("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=90329971-0f13-469f-80ef-49901c457f70"
                      , data=request_string, headers=headers)
    print(r.text)


def test_notify():
    datajson = {
        "msgtype": "text",
        "text": {
            "content": "测试消息，请忽略",
            "mentioned_mobile_list": ["18616365805"]
        }
    }
    request_string = json.dumps(datajson)
    r = requests.post("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ed05a5c1-3043-4107-89cd-5a412a197428"
                      , data=request_string, headers=headers)
    print(r.text)


if __name__ == "__main__":
    # send_wechat(GithubManager.generate_markdown_report())
    test_notify()
