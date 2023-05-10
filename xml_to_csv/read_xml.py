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
RELATIONSHIP_HEADERS = ["source", "destination", "description"]


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

    def _remove_tags(self, string: str) -> str:
        string = re.sub(r"{{dlc\|a}}", "(Added in Afterbirth)", string, re.IGNORECASE)
        string = re.sub(r"{{dlc\|na}}", "(Removed in Afterbirth)", string, re.IGNORECASE)
        string = re.sub(r"{{dlc\|a\+}}", "(Added in Afterbirth+)", string, re.IGNORECASE)
        string = re.sub(r"{{dlc\|na\+}}", "(Removed in Afterbirth+)", string, re.IGNORECASE)
        string = re.sub(r"{{dlc\|ana\+}}", "(Added in Afterbirth, Removed in Afterbirth+)", string, re.IGNORECASE)
        string = re.sub(r"{{dlc\|r}}", "(Added in Repentance)", string, re.IGNORECASE)
        string = re.sub(r"{{dlc\|nr}}", "(Removed in Repentance)", string, re.IGNORECASE)
        string = re.sub(r"{{dlc\|anr}}", "(Added in Afterbirth, Removed in Repentance)", string, re.IGNORECASE)
        string = re.sub(r"{{dlc\|a\+nr}}", "(Added in Afterbirth+, Removed in Repentance)", string, re.IGNORECASE)
        string = re.sub(r"\[\[(.+?)\]\]", r"\g<1>", string, flags=re.IGNORECASE)  # TODO needs to be more sophisticated
        return re.sub(r"{{[iectrspam]\|(.+?)}}", r"\g<1>", string, flags=re.IGNORECASE)  # TODO doesnt match all of them

    def _format_list(self, string: list, indentation: int = 0) -> str:
        output = ""
        tabs = "&emsp;" * indentation
        for line in string:
            if isinstance(line, str):
                output += f"{tabs}- {self._remove_tags(line)}<br>"
            else:
                output += self._format_list(line, indentation + 1)
        return output

    @staticmethod
    def _dig(nested, depth) -> list:
        for _ in range(0, (depth - 1)):
            nested = nested[-1]
        return nested

    def _parse_list(self, list_string: str, format_flag: bool = False) -> list:
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
        if format_flag:
            return self._format_list(output)
        return output

    def _infobox_get(self, text: str, regex: re.Pattern) -> str:
        return self._remove_tags(regex.search(text)[1]) if regex.search(text) is not None else None

    def _list_get(self, text: str, regex: re.Pattern, format_flag: bool = False) -> list:
        return self._parse_list(regex.search(text)[1], format_flag) if regex.search(text) is not None else None

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
        character_names = list(dict.fromkeys(re.findall(r"{{c\|(.*?)}}", challenges_page)))
        for i, name in enumerate(character_names):
            if name == "???":
                character_names[i] = "??? (Character)"
            elif name == "Jacob and Esau":
                character_names[i] = "Jacob & Esau"
        return character_names

    def get_all_items(self) -> list:
        item_names = self._get_item_names()
        tags = self.soup.find_all("title")
        item_data = []
        for tag in tags:
            if tag.text not in item_names:
                continue

            item_text = tag.find_parent("page").find("text").text

            item_id = self._infobox_get(item_text, ID_REGEX)
            if item_id is None:
                continue

            item_data.append(
                [
                    tag.text,
                    f"I{item_id}",
                    self._infobox_get(item_text, QUOTE_REGEX),
                    self._infobox_get(item_text, DESCRIPTION_REGEX),
                    self._infobox_get(item_text, ITEM_QUALITY_REGEX),
                    self._infobox_get(item_text, UNLOCK_REGEX),
                    self._list_get(item_text, EFFECTS_REGEX, True),
                    self._list_get(item_text, NOTES_REGEX, True),
                ]
            )
            self.id_lookup[tag.text.lower()] = f"I{item_id}"
            self.synergies[tag.text] = self._list_get(item_text, SYNERGIES_REGEX)
            self.interactions[tag.text] = self._list_get(item_text, INTERACTIONS_REGEX)
        return item_data

    def get_all_trinkets(self) -> list:
        trinket_names = self._get_trinket_names()
        tags = self.soup.find_all("title")
        trinket_data = []

        for tag in tags:
            if tag.text not in trinket_names:
                continue
            trinket_text = tag.find_parent("page").find("text").text

            trinket_id = self._infobox_get(trinket_text, ID_REGEX)
            if trinket_id is None:
                continue

            trinket_data.append(
                [
                    tag.text,
                    f"T{trinket_id}",
                    self._infobox_get(trinket_text, POOL_REGEX),
                    self._infobox_get(trinket_text, QUOTE_REGEX),
                    self._infobox_get(trinket_text, DESCRIPTION_REGEX),
                    self._infobox_get(trinket_text, TAGS_REGEX),
                    self._infobox_get(trinket_text, UNLOCK_REGEX),
                    self._list_get(trinket_text, EFFECTS_REGEX, True),
                    self._list_get(trinket_text, NOTES_REGEX, True),
                ]
            )
            self.id_lookup[tag.text.lower()] = f"T{trinket_id}"
            self.synergies[tag.text] = self._list_get(trinket_text, SYNERGIES_REGEX)
            self.interactions[tag.text] = self._list_get(trinket_text, INTERACTIONS_REGEX)
        return trinket_data

    def get_all_characters(self) -> list:
        character_names = self._get_character_names()
        tags = self.soup.find_all("title")
        character_data = []
        for tag in tags:
            if tag.text not in character_names:
                continue
            character_text = tag.find_parent("page").find("text").text

            character_id = self._infobox_get(character_text, ID_REGEX)

            if tag.text == "Jacob & Esau":
                character_id = 1
            elif tag.text == "Tainted Eden":
                character_id = 11
            elif character_id is None:
                continue

            character_data.append(
                [
                    tag.text,
                    f"C{character_id}",
                ]
            )
            self.id_lookup[tag.text.lower()] = f"C{character_id}"
        character_data.append(["Dark Judas", 12])
        self.id_lookup["dark judas"] = "C12"
        return character_data

    def get_relationships(self, data: dict):
        output = []
        for source, relationship_data in data.items():
            if relationship_data is None:
                continue
            for relationship in relationship_data:
                destinations = re.findall(r"{{[ict]\|(1=)?(.+?)(\|.+?)?}}", relationship[0], re.IGNORECASE)
                for dest in destinations:
                    if dest[1].lower() == "number two":
                        dest = ("", "no. 2", "")
                    elif dest[1].lower() == "money {{=":
                        dest = ("", "money = power", "")
                    elif dest[1].lower() == "jacob and esau":
                        dest = ("", "jacob & esau", "")
                    elif dest[1].lower() == "???":
                        dest = ("", "??? (Character)", "")
                    elif dest[1].lower() == "tainted soul":
                        dest = ("", "tainted forgotten", "")
                    elif dest[1].lower() == "dead tainted lazarus":
                        dest = ("", "tainted lazarus", "")
                    elif dest[1].lower() in ("broken shovel 1", "broken shovel 2"):
                        continue
                    output.append(
                        [
                            self.id_lookup[source.lower().strip()],
                            self.id_lookup[dest[1].lower().strip()],
                            self._format_list(relationship),
                        ]
                    )
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
    converter.write_to_csv(converter.get_relationships(converter.synergies), RELATIONSHIP_HEADERS, "synergies")
    converter.write_to_csv(converter.get_relationships(converter.interactions), RELATIONSHIP_HEADERS, "interactions")
