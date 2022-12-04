#!/usr/bin/python3
import json
import re
from bs4 import BeautifulSoup

item_regex = re.compile(r"content =(.*?)}}", flags=re.DOTALL)


def get_soup(path: str) -> BeautifulSoup:
    with open(path, encoding="utf-8", mode="r") as f:
        xml = f.read()
    return BeautifulSoup(xml, "xml")


def get_all_items(path: str):
    soup = get_soup(path)
    item_names = get_item_names(path)
    tags = soup.find_all("title")
    item_dict = {}
    for tag in tags:
        if tag.text in item_names:
            item_dict[tag.text] = tag.find_parent("page").find("text").text
    with open("items.json", encoding="utf-8", mode="w") as output:
        json.dump(item_dict, output)


def get_item_names(path: str):
    soup = get_soup(path)
    collection = soup.find("title", text="Collection Page (Repentance)").find_parent("page").find("text").text
    return [x.strip() for x in item_regex.search(collection)[1].replace("\n", "").split(",")]


if __name__ == "__main__":
    # print(get_item_names("../data.xml"))
    get_all_items("../data.xml")
