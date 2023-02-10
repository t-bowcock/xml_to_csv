#!/usr/bin/python3
"""
Reads the XML dump and creates CSV files containing the relevant data
"""
import csv
import re
from bs4 import BeautifulSoup

ITEM_REGEX = re.compile("content =(.*?)}}", flags=re.DOTALL)

ID_REGEX = re.compile(r"\| id\s+= ([0-9]+)")
QUOTE_REGEX = re.compile(r"\| quote\s+= (.*)")
DESCRIPTION_REGEX = re.compile(r"\| description\s+= (.*)")
ITEM_QUALITY_REGEX = re.compile(r"\| quality\s+= ([0-9]{1})")
UNLOCK_REGEX = re.compile(r"\| unlocked by\s+= (.*)")
POOL_REGEX = re.compile(r"\| pool\s+= (.*)")
TAGS_REGEX = re.compile(r"\| tags\s+= (.*)")
DLC_REGEX = re.compile(r"\| dlc\s+= (.*)")
HEALTH_REGEX = re.compile(r"\| health\s+= (.*)")
DAMAGE_REGEX = re.compile(r"\| damage\s+= (.*)")
TEARS_REGEX = re.compile(r"\| tears\s+= (.*)")
SHOT_SPEED_REGEX = re.compile(r"\| shot speed\s+= (.*)")
RANGE_REGEX = re.compile(r"\| range\s+= (.*)")
LUCK_REGEX = re.compile(r"\| luck\s+= (.*)")
SPEED_REGEX = re.compile(r"\| speed\s+= (.*)")
PICKUPS_REGEX = re.compile(r"\| pickups\s+= (.*)")
COLLECTIBLES_REGEX = re.compile(r"\| collectibles\s+= (.*)")

EFFECTS_REGEX = re.compile(r"==\s?Effects?\s?==\n+(.*?)\n\n==", flags=re.DOTALL)
NOTES_REGEX = re.compile(r"==\s?Notes\s?==\n+(.*?)\n\n==", flags=re.DOTALL)
SYNERGIES_REGEX = re.compile(r"==\s?Synergies\s?==\n+(.*?)\n\n==", flags=re.DOTALL)
INTERACTIONS_REGEX = re.compile(r"==\s?Interactions\s?==\n+(.*?)\n\n==", flags=re.DOTALL)

BULLET_REGEX = re.compile(r"(\*+)")

ITEM_HEADERS = ["name", "id", "quote", "description", "quality", "unlock", "effects", "notes"]
TRINKET_HEADERS = ["name", "id", "pool", "quote", "description", "tags", "unlock", "effects", "notes"]
CHARACTER_HEADERS = ["name", "id"]
RELATIONHSIP_HEADERS = ["source", "destination", "description"]


class XMLToCSV:
    def __init__(self, xml_path: str, output_path: str = None) -> None:
        self.soup = self._get_soup(xml_path)

        self.id_lookup = {}
        self.synergies = {}
        self.interactions = {}
        self.output_path = output_path

    def _get_soup(self, path: str):
        with open(path, encoding="utf-8", mode="r") as xml_file:
            xml = xml_file.read()
        return BeautifulSoup(xml, "xml")

    @staticmethod
    def _dig(nested, depth) -> list:
        for _ in range(0, (depth - 1)):
            nested = nested[-1]
        return nested

    @staticmethod
    def _parse_dlc_tags(string):
        # TODO do it
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

    @staticmethod
    def _parse_string(string: str) -> str:
        # TODO turn dlc tags to text
        # TODO decide how relationships are handled
        # TODO parse any html (seen some <br> tags)
        re.sub(r"\[\[|\]\]", "", string)
        re.sub(r"{{[erspam]\|(.*?)}}", r"\g<1>", string, flags=re.IGNORECASE)

    def _parse_list(self, list_string: str) -> list:
        split_list = BULLET_REGEX.split(list_string)
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
                    self._dig(output[one_star_counter], previous).append(line)
                elif new > previous:
                    self._dig(output[one_star_counter], previous).append([line])
                elif new < previous:
                    self._dig(output[one_star_counter], new).append(line)
            previous = new
        return output

    @staticmethod
    def _infobox_get(text: str, regex: re.Pattern) -> str:
        return regex.search(text)[1] if regex.search(text) is not None else None

    def _list_get(self, text: str, regex: re.Pattern) -> list:
        return self._parse_list(regex.search(text)[1]) if regex.search(text) is not None else None

    def _get_item_names(self):
        collection = self.soup.find("title", text="Collection Page (Repentance)").find_parent("page").find("text").text
        return [
            x.strip()
            for x in ITEM_REGEX.search(collection)[1].replace("\n", "").replace("Number Two", "No. 2").split(",")
        ]

    @staticmethod
    def _get_trinket_names() -> list:
        # TODO look at reading this from the wiki
        with open("../trinkets.txt", encoding="utf-8", mode="r") as trinket_file:
            names = [line.strip() for line in trinket_file]
        return names

    def _get_character_names(self) -> list:
        challenges_page = self.soup.find("title", text="Characters").find_parent("page").find("text").text
        return list(dict.fromkeys(re.findall(r"{{c\|(.*?)}}", challenges_page)))

    def get_all_items(self) -> list:
        item_names = self._get_item_names()
        tags = self.soup.find_all("title")
        item_data = []
        for tag in tags:
            if tag.text in item_names:

                item_text = tag.find_parent("page").find("text").text

                item_id = self._infobox_get(item_text, ID_REGEX)
                if item_id is None:
                    continue

                item_data.append(
                    [
                        tag.text,
                        item_id,
                        self._infobox_get(item_text, QUOTE_REGEX),
                        self._infobox_get(item_text, DESCRIPTION_REGEX),
                        self._infobox_get(item_text, ITEM_QUALITY_REGEX),
                        self._infobox_get(item_text, UNLOCK_REGEX),
                        self._list_get(item_text, EFFECTS_REGEX),
                        self._list_get(item_text, NOTES_REGEX),
                    ]
                )
                self.id_lookup[tag.text.lower()] = item_id
                self.synergies[tag.text] = self._list_get(item_text, SYNERGIES_REGEX)
                self.interactions[tag.text] = self._list_get(item_text, INTERACTIONS_REGEX)
        return item_data

    def get_all_trinkets(self) -> list:
        trinket_names = self._get_trinket_names()
        tags = self.soup.find_all("title")
        trinket_data = []

        for tag in tags:
            if tag.text in trinket_names:

                trinket_text = tag.find_parent("page").find("text").text

                trinket_id = self._infobox_get(trinket_text, ID_REGEX)
                if trinket_id is None:
                    continue

                trinket_data.append(
                    [
                        tag.text,
                        trinket_id,
                        self._infobox_get(trinket_text, POOL_REGEX),
                        self._infobox_get(trinket_text, QUOTE_REGEX),
                        self._infobox_get(trinket_text, DESCRIPTION_REGEX),
                        self._infobox_get(trinket_text, TAGS_REGEX),
                        self._infobox_get(trinket_text, UNLOCK_REGEX),
                        self._list_get(trinket_text, EFFECTS_REGEX),
                        self._list_get(trinket_text, NOTES_REGEX),
                    ]
                )
                self.id_lookup[tag.text.lower()] = trinket_id
                self.synergies[tag.text] = self._list_get(trinket_text, SYNERGIES_REGEX)
                self.interactions[tag.text] = self._list_get(trinket_text, INTERACTIONS_REGEX)
        return trinket_data

    def get_all_characters(self) -> list:
        character_names = self._get_character_names()
        tags = self.soup.find_all("title")
        character_data = []
        for tag in tags:
            if tag.text in character_names:

                character_text = tag.find_parent("page").find("text").text

                character_id = self._infobox_get(character_text, ID_REGEX)
                if character_id is None:
                    continue

                character_data.append(
                    [
                        tag.text,
                        character_id,
                    ]
                )
                self.id_lookup[tag.text.lower()] = character_id
        return character_data

    def get_relationships(self, data: dict):
        output = []
        for source, relationship_data in data.items():
            if relationship_data is None:
                continue
            for relationship in relationship_data:
                destinations = re.findall(r"{{i\|(1=)?(.+?)(\|.+?)?}}", relationship[0], re.IGNORECASE)
                for dest in destinations:
                    if dest[1].lower() == "number two":
                        dest = ("", "no. 2", "")
                    if dest[1].lower() == "money {{=":
                        dest = ("", "money = power", "")
                    if dest[1].lower() in ("broken shovel 1", "broken shovel 2"):
                        continue
                    output.append([self.id_lookup[source.lower()], self.id_lookup[dest[1].lower()], relationship])
        return output

    @staticmethod
    def write_to_csv(data: list, headers: list, filename: str):
        with open(f"{filename}.csv", encoding="utf-8", mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)
            writer.writerows(data)


if __name__ == "__main__":
    converter = XMLToCSV("../data.xml")
    items = converter.get_all_items()
    trinkets = converter.get_all_trinkets()
    characters = converter.get_all_characters()
    converter.write_to_csv(items, ITEM_HEADERS, "items")
    converter.write_to_csv(trinkets, TRINKET_HEADERS, "trinkets")
    converter.write_to_csv(characters, CHARACTER_HEADERS, "characters")
    converter.write_to_csv(converter.get_relationships(converter.synergies), RELATIONHSIP_HEADERS, "synergies")
    converter.write_to_csv(converter.get_relationships(converter.interactions), RELATIONHSIP_HEADERS, "interactions")
