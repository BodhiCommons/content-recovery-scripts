"""URL scraper."""

import time
from pathlib import Path

import requests
import requests.exceptions
from bs4 import BeautifulSoup as bs
from bs4 import NavigableString, Tag


class BodhiSnapShot:
    """IA snapshot."""

    def __init__(
        self,
        url: str = "http://bodhicommons.org",
        time_stamp: str = "20230331041108",
    ) -> None:
        """Initialize bodhi snapshot."""
        self.headers: dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"
        }
        self.url: str = url
        self.time_stamp: str = time_stamp
        self.output_format: str = "json"
        self.web_archive_url: str = (
            f"https://web.archive.org/web/{self.time_stamp}/{self.url}?page="
        )
        self.article_urls: list[str] = []

    def fire_request(self) -> None:
        """Fire request."""
        self.request: str = requests.get(
            self.web_archive_url,
            headers=self.headers,
            timeout=10,
        ).text

    def make_soup(self) -> None:
        """Make soup."""
        self.soup = bs(self.request, "lxml")

    def find_main_block(self) -> None:
        """Find main block.

        Raises
        ------
            TypeError: If main block is not found.

        """
        main_block: Tag | NavigableString | None = self.soup.find(
            id="block-lenin-content"
        )

        if not isinstance(main_block, Tag):
            error_message = "Could not find main block"
            raise TypeError(error_message)

        self.main_block: Tag = main_block

    def find_articles(self) -> None:
        """Find articles."""
        self.article_list = self.main_block.find_all(class_="views-row")

    def get_article_urls(self) -> None:
        """Get article urls."""
        for article in self.article_list:
            a_ = article.find("a")
            if a_ is not None:
                self.article_urls.append(a_.attrs["href"])

    def __write_urls_to_file(self, page_number: int) -> None:
        """Append urls to file."""
        with Path(f"page_{page_number}_urls.txt").open("w+", encoding="utf-8") as page_:
            for article_url in self.article_urls:
                page_.write(f"{article_url}\n")

    def __pageinate_url(self, page_number: int) -> None:
        self.web_archive_url = f"https://web.archive.org/web/{self.time_stamp}/{self.url}?page={page_number}"

    def scrape_urls(self) -> None:
        """Scrape urls."""
        start_page = 19
        end_page = 65
        for page_number in range(start_page, end_page + 1):
            self.__pageinate_url(page_number=page_number)
            try:
                self.fire_request()
                self.make_soup()
                self.find_main_block()
                self.find_articles()
                self.get_article_urls()
                self.__write_urls_to_file(page_number=page_number)
            except requests.exceptions.RequestException as e:
                print(e)
        time.sleep(10)


if __name__ == "__main__":
    bodhi_snapshot = BodhiSnapShot()
    bodhi_snapshot.scrape_urls()
