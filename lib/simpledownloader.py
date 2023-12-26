#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests

class SimpleDownloader:
    def get_url(self, url:str):
        d = requests.get(url)
        resp_data = {
            "encoding": d.encoding,
            "headers": d.headers,
        }
        return d.status_code, d.content, resp_data


if __name__ == "__main__":
    dl = SimpleDownloader()
    status, data, info = dl.get_url("http://192.168.0.15:9090/axs")
    print(status)
    print(info)