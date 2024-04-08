#!/usr/bin/env python3

import collections
import configparser
import json
import pathlib
import urllib.request
import xml.etree.ElementTree


def convert(x):
    try:
        x = int(x)
    except ValueError:
        pass
    return x


def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = collections.defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v)
                        for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = convert(text)
    return d


def mkurl(base: str, api_key: str, page: int = 1) -> str:
    return f"{base}?page={page}&api_key={api_key}"


def curl(url: str) -> bytes:
    print(f"Fetching {url}...")
    with urllib.request.urlopen(
        urllib.request.Request(
            url,
            headers={
                "accept": "*/*",
                "user-agent": "custom",
            },
        )
    ) as response:
        return response.read()


def curlxml(url: str) -> str:
    return etree_to_dict(xml.etree.ElementTree.fromstring(curl(url)))


def main() -> None:
    config = configparser.ConfigParser()
    config.read("creds.ini")
    api_key = config["main"]["api_key"]

    account = curlxml(mkurl("https://openhub.net/accounts/alonbl.xml", api_key))
    positions = []
    for page in range(1, 100):
        pos1 = curlxml(mkurl("https://openhub.net/accounts/alonbl/positions.xml", api_key, page))
        if pos1["response"]["items_returned"] == 0:
            break
        x = pos1["response"]["result"]["position"]
        if isinstance(x, dict):
            x = [x]
        positions.extend(x)

    pathlib.Path("out").mkdir(exist_ok=True)
    with open("out/account.json", "w") as f:
        f.write(json.dumps(account["response"]["result"]["account"]))
    with open("out/positions.json", "w") as f:
        f.write(json.dumps(positions))

    with open("out/positions.txt", "w") as f:
        for entry in sorted(positions, key=lambda a: a["project"]["name"]):
            f.write(
                "\n".join((
                    f"{entry['project']['name']}",
                    f"{'':10}{'Description:':15}{entry['project']['description']}",
                    f"{'':10}{'Commits:':15}{entry.get('commits') or -1}",
                )) + "\n"
            )


if __name__ == "__main__":
    main()
