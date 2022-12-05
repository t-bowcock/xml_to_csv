#!/usr/bin/python3
import json
import re
from bs4 import BeautifulSoup

item_regex = re.compile("content =(.*?)}}", flags=re.DOTALL)
item_id_regex = re.compile(r"\| id\s+= ([0-9]+)")
item_quote_regex = re.compile(r"\| quote\s+= (.*)")
item_description_regex = re.compile(r"\| description\s+= (.*)")
item_quality_regex = re.compile(r"\| quality\s+= ([0-9]{1})")
item_unlock_regex = re.compile(r"\| unlocked by\s+= (.*)")
item_effects_regex = re.compile(r"==\s?Effects\s?==\n+(.*?)\n\n", flags=re.DOTALL)
item_notes_regex = re.compile(r"==\s?Notes\s?==\n+(.*?)\n\n", flags=re.DOTALL)
item_synergies_regex = re.compile(r"==\s?Synergies\s?==\n+(.*?)\n\n", flags=re.DOTALL)
item_interactions_regex = re.compile(r"==\s?Interactions\s?==\n+(.*?)\n\n", flags=re.DOTALL)

list_regex = re.compile(r"\*+(.*?)\*", flags=re.DOTALL)


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

            item_text = tag.find_parent("page").find("text").text

            item_id = item_id_regex.search(item_text)[1] if item_id_regex.search(item_text) is not None else None
            if item_id is None:
                continue
            item_quote = (
                item_quote_regex.search(item_text)[1] if item_quote_regex.search(item_text) is not None else None
            )

            item_description = (
                item_description_regex.search(item_text)[1]
                if item_description_regex.search(item_text) is not None
                else None
            )

            item_quality = (
                item_quality_regex.search(item_text)[1] if item_quality_regex.search(item_text) is not None else None
            )

            item_unlock = (
                item_unlock_regex.search(item_text)[1] if item_unlock_regex.search(item_text) is not None else None
            )

            item_effects = (
                item_effects_regex.search(item_text)[1] if item_effects_regex.search(item_text) is not None else None
            )

            item_notes = (
                item_notes_regex.search(item_text)[1] if item_notes_regex.search(item_text) is not None else None
            )

            item_synergies = (
                item_synergies_regex.search(item_text)[1]
                if item_synergies_regex.search(item_text) is not None
                else None
            )

            item_interactions = (
                item_interactions_regex.search(item_text)[1]
                if item_interactions_regex.search(item_text) is not None
                else None
            )
            item_dict[tag.text] = {
                "ID": item_id,
                "quote": item_quote,
                "description": item_description,
                "quality": item_quality,
                "unlock": item_unlock,
                "effects": item_effects,
                "notes": item_notes,
                "synergies": item_synergies,
                "interactions": item_interactions,
            }
    with open("items.json", encoding="utf-8", mode="w") as output:
        json.dump(item_dict, output)


def get_item_names(path: str):
    soup = get_soup(path)
    collection = soup.find("title", text="Collection Page (Repentance)").find_parent("page").find("text").text
    return [x.strip() for x in item_regex.search(collection)[1].replace("\n", "").split(",")]


if __name__ == "__main__":
    # print(get_item_names("../data.xml"))
    get_all_items("../data.xml")
