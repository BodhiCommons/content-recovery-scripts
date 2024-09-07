
from pathlib import Path
import requests
import time

from bs4 import BeautifulSoup as bs, NavigableString, Tag


class BodhiSnapShot:
    """IA snapshot."""

    def __init__(self, url: str = "http://bodhicommons.org", time_stamp: str = "20230331041108",) -> None:
        self.headers: dict[str, str] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
        }
        self.url: str = url
        self.time_stamp: str = time_stamp
        self.output_format: str = "json"
        self.web_archive_url: str = f"https://web.archive.org/web/{self.time_stamp}/{self.url}?page="
        self.article_urls: list[str] = []

    def fire_request(self) -> None:
        self.request: str = requests.get(self.web_archive_url, headers=self.headers).text

    def make_soup(self) -> None:
        self.soup = bs(self.request,'lxml')

    def find_main_block(self) -> None:
        main_block: Tag | NavigableString | None = self.soup.find(id="block-lenin-content")

        if not isinstance(main_block, Tag):
            raise ValueError("Could not find main block")

        self.main_block: Tag = main_block
            

    def find_articles(self) -> None:
        self.article_list = self.main_block.find_all(class_="views_row")

    def get_article_urls(self) -> None:
        for article in self.article_list:
            a_ = article.find('a')
            if a_ is not None:
                self.article_urls.append(a_.attrs['href'])


    def __write_urls_to_file(self, page_number: int) -> None:
        """Append urls to file."""
        with Path(f"page_{page_number}_urls.txt", "w+") as page_:
            for article_url in self.article_urls:
                page_.write_text(f"{article_url}\n")


    def __pageinate_url(self, page_number: int) -> None:
        self.web_archive_url = f"https://web.archive.org/web/{self.time_stamp}/{self.url}?page={page_number}"


    def scrape_urls(self) -> None:
        for page_number in range(0, 66):
            self.__pageinate_url(page_number=page_number)
            try:
                self.fire_request()
                self.make_soup()
                self.find_main_block()
                self.find_articles()
                self.get_article_urls()
                self.__write_urls_to_file(page_number=page_number)
            except Exception as e:
                print(e)
        time.sleep(1)


if __name__ == "__main__":
    bodhi_snapshot = BodhiSnapShot()
    bodhi_snapshot.scrape_urls()