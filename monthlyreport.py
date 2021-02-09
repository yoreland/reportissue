import datetime
import time


if __name__ == "__main__":
    delta = datetime.datetime.now() - (datetime.datetime.today() + datetime.timedelta(days=-2))
    # print((datetime.datetime.today() + datetime.timedelta(days=-2)).timestamp())
    print(delta.total_seconds() / 3600)