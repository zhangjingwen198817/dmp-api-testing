# -*- coding:utf-8 -*-
import sys
import urllib
import urllib2
import json
import time
import re

INSTALL_URL = [
    "v3/install/umc",
    "install/umc",
]


class umcHander:
    def __init__(self, addr, port):
        self.logged = False
        self._header = {}
        self.addr = addr
        self.port = port

    def get_header(self):
        return self._header

    def full_url(self, short_url):
        return "http://{0}:{1}/{2}".format(self.addr, self.port, short_url)

    def post(self, short_url, data):
        timer = 0
        for i in range(10):
            try:
                req = urllib2.Request(self.full_url(short_url), data=urllib.urlencode(data), headers=self.get_header())
                res = urllib2.urlopen(req)
                return res.read()
            except Exception as e:
                if i >= 9:
                    print("[error]Post info failed: {0}".format(e))
                    exit(1)
                else:
                    time.sleep(3)
                    timer += 3
        print("Post cost : {0}".format(timer))

    def get(self, short_url):
        for i in range(10):
            try:
                req = urllib2.Request(self.full_url(short_url), headers=self.get_header())
                res = urllib2.urlopen(req)
                return res.read()
            except Exception as e:
                if i >= 9:
                    print("[error]Get info failed: {0}".format(e))
                    exit(1)
                else:
                    time.sleep(3)

    def login(self):
        if self.logged:
            return
        try:
            res = self.post("user/login",
                            data={
                                "user": "admin",
                                "password": "admin",
                            })
            token = json.loads(res).get("token")
            self._header["authorization"] = token
            self.logged = True
        except urllib.error.HTTPError as e:
            print(e.code)
            print(e.info())

    def post_wait_progress(self, short_url, data):
        try:
            if short_url not in INSTALL_URL:
                self.login()
            res = self.post(short_url, data)
        except urllib2.URLError as e:
            print(str(e))
        except Exception as e:
            error_message = e.read()
            print("[error]connect to umc failed:" + error_message)
            return
        j = json.loads(res)
        progress_url = "progress?id={0}".format(j["progress_id"])
        step = 0
        print("")
        print("====================START====================")
        while True:
            try:
                res = self.get(progress_url)
            except Exception as e:
                print(str(e))
                error_message = e.read()
                if error_message == "no user":
                    self.login()
                    continue
                else:
                    print("[error]connect to umc failed:" + error_message)
                    return
            progress_data = json.loads(res)
            done = progress_data.get("doneMsg", "").encode('utf-8')
            err = progress_data.get("err", "").encode('utf-8')
            if "Desc" in progress_data.keys():
                desc = progress_data.get("Desc", "").encode('utf-8')
            else:
                desc = progress_data.get("desc", "").encode('utf-8')
            # print total
            if step == 0:
                print(desc)
                step = step + 1
            # print steps
            steps = progress_data["steps"]
            current_step = progress_data.get("step", 0)
            while step <= current_step and current_step > 0:
                print(steps[step - 1].encode('utf-8'))
                step = step + 1
            if done:
                print(done)
                break
            if err:
                print(err)
                exit(1)
            time.sleep(1)
        print("=====================END=====================")

    def run_from_json(self, data):
        try:
            self.post_wait_progress(data["url"], data["json"])
        except Exception as e:
            print(str(e))


def replace_rpm_version(v, rpm_name):
    return re.sub("-\d{1,2}.\d{1,2}.\d{1,2}.\d{1,2}-", "-{0}-".format(v), rpm_name)


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    umc_addr = sys.argv[1]
    umc_port = sys.argv[2]
    data_json_file = sys.argv[3]
    u = umcHander(umc_addr, umc_port)
    with open(data_json_file) as f:
        data_json = json.loads(f.read())
        if isinstance(data_json, list):
            try:
                for data in data_json:
                    u.run_from_json(data)
            except Exception as e:
                print(str(e))
        else:
            print("data json is invalid")
