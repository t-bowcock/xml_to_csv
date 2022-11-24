from bs4 import BeautifulSoup


def get_soup(path: str) -> BeautifulSoup:
    with open(path, encoding="utf-8", mode="r") as f:
        xml = f.read()
    return BeautifulSoup(xml, "xml")


def get_all_tag(path: str, tag: str):
    soup = get_soup(path)
    tags = soup.find_all(tag)
    print(len(tags))
    with open("tags.txt", "w") as output:
        for t in tags:
            if ":" not in t.text:
                output.write(f"{t.text}\n")


if __name__ == "__main__":
    get_all_tag("data.xml", "title")
