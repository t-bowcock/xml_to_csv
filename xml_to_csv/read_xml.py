#!/usr/bin/python3
import csv
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

bullet_regex = re.compile(r"(\*+)")

ITEM_HEADERS = ["name", "ID", "quote", "description", "quality", "unlock", "effects", "notes"]
RELATIONHSIP_HEADERS = ["item", "node", "relationship"]


def get_soup(path: str) -> BeautifulSoup:
    with open(path, encoding="utf-8", mode="r") as f:
        xml = f.read()
    return BeautifulSoup(xml, "xml")


def dig(nested, depth):
    for _ in range(0, (depth - 1)):
        nested = nested[-1]
    return nested


def parse_dlc_tags(string):
    tags = re.findall(r"{{dlc\|(.+?)}}", string, re.IGNORECASE)
    for tag in tags:
        # a, a+, r are all tags that represent the change being added in DLC
        # n<tag> means the change was removed in a later dlc
        if re.match(r"a\+", tag[1]):
            pass
        elif re.match("a", tag[1]):
            pass
        else:
            pass


def parse_string(string: str) -> str:
    # TODO turn dlc tags to text
    # TODO decide how relationships are handled
    # TODO parse any html (seen some <br> tags)
    re.sub(r"\[\[|\]\]", "", string)
    re.sub(r"{{[erspam]\|(.*?)}}", r"\g<1>", string, flags=re.IGNORECASE)


def parse_list(list_string: str) -> list:
    split_list = bullet_regex.split(list_string)
    output = []
    previous = 0
    one_star_counter = -1
    for i in range(1, len(split_list), 2):
        new = len(split_list[i])
        line = split_list[i + 1].strip()
        if new == 1:
            one_star_counter += 1
            output.append([line])
        else:
            if new == previous:
                dig(output[one_star_counter], previous).append(line)
            elif new > previous:
                dig(output[one_star_counter], previous).append([line])
            elif new < previous:
                dig(output[one_star_counter], new).append(line)
        previous = new
    return output


def get_all_items(path: str) -> list:
    soup = get_soup(path)
    item_names = get_item_names(path)
    tags = soup.find_all("title")
    item_data = []
    synergy_data = {}
    interaction_data = {}
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
                parse_list(item_effects_regex.search(item_text)[1])
                if item_effects_regex.search(item_text) is not None
                else None
            )

            item_notes = (
                parse_list(item_notes_regex.search(item_text)[1])
                if item_notes_regex.search(item_text) is not None
                else None
            )

            item_synergies = (
                parse_list(item_synergies_regex.search(item_text)[1])
                if item_synergies_regex.search(item_text) is not None
                else None
            )

            item_interactions = (
                parse_list(item_interactions_regex.search(item_text)[1])
                if item_interactions_regex.search(item_text) is not None
                else None
            )
            item_data.append(
                [
                    tag.text,
                    item_id,
                    item_quote,
                    item_description,
                    item_quality,
                    item_unlock,
                    item_effects,
                    item_notes,
                ]
            )
            synergy_data[tag.text] = item_synergies
            interaction_data[tag.text] = item_interactions
    return item_data, synergy_data, interaction_data


def get_item_names(path: str):
    soup = get_soup(path)
    collection = soup.find("title", text="Collection Page (Repentance)").find_parent("page").find("text").text
    return [x.strip() for x in item_regex.search(collection)[1].replace("\n", "").split(",")]


def get_relationships(data: dict):
    output = []
    for item, relationship_data in data.items():
        if relationship_data is None:
            continue
        for relationship in relationship_data:
            other_nodes = re.findall(r"{{i\|(.+?)}}", relationship[0], re.IGNORECASE)
            for node in other_nodes:
                output.append([item, node, relationship])
    return output


def write_to_csv(data: list, headers: list, filename: str):
    with open(f"{filename}.csv", encoding="utf-8", mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerows(data)


if __name__ == "__main__":
    items, synergies, interactions = get_all_items("../data.xml")
    write_to_csv(items, ITEM_HEADERS, "items")
    write_to_csv(get_relationships(synergies), RELATIONHSIP_HEADERS, "synergies")
    write_to_csv(get_relationships(interactions), RELATIONHSIP_HEADERS, "interactions")
