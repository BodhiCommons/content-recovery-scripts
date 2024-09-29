"""URL scraper."""

import time
from pathlib import Path

import orjson
import requests
import requests.exceptions
from bs4 import BeautifulSoup as bs
from bs4.element import NavigableString, Tag
from langdetect import detect


class PageSnapShot:
    """InternetArchive Page snapshot."""

    def __init__(
        self,
        url_directory: str = "",
        json_db_name: str = "backup.json",
    ) -> None:
        """Initialize bodhi snapshot."""
        self.headers: dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"
        }
        self.url_files_directory: Path = Path(url_directory)
        self.output_format: str = "json"
        self.article_urls: list[str] = []
        self.json_db_name: Path = Path(json_db_name)
        if not self.json_db_name.exists():
            self.json_db_name.touch()
        self.json_db: list[dict[str, str | list[str]]] = self.__load_json_db()
        self.article_urls_in_db: set[str] = {
            article["url"]
            for article in self.json_db
            if isinstance(article["url"], str)
        }
        self.__load_all_article_urls()
        self.__scrape_all_urls()

    def __load_json_db(self) -> list[dict[str, str | list[str]]]:
        """Load json db.

        Returns:
            dict[str, dict[str, str]]: Json db.

        """
        try:
            with self.json_db_name.open("rb+") as json_file:
                return orjson.loads(json_file.read())
        except orjson.JSONDecodeError:
            return []

    def __load_all_article_urls(self) -> None:
        """Load urls."""
        for file_ in self.url_files_directory.iterdir():
            if (
                file_.is_file()
                and "_urls.txt" in file_.name
                and "beta" not in file_.name
            ):
                article_urls: list[str] = file_.read_text().strip().split("\n")
                self.article_urls.extend(article_urls)

    def __scrape_all_urls(self) -> None:
        """Scrape all urls."""
        articles_to_be_scraped: set[str] = {
            article
            for article in self.article_urls
            if article not in self.article_urls_in_db
        }
        total_articles: int = len(articles_to_be_scraped)
        for index, article_url in enumerate(articles_to_be_scraped, start=1):
            try:
                if "beta.bodhicommons.org" in article_url:
                    print("Beta link skipped.")
                    continue
                self.fire_request(article_url=article_url)
                self.make_soup()
                if index % 4 == 0:
                    time.sleep(60)
                article: dict[str, str | list[str]] = self.fetch_content(
                    article_url=article_url
                )
                if article:
                    self.json_db.append(article)
                self.__write_json_db_to_disk()
                print(
                    f"Finished writing {index} articles out of {total_articles} articles."
                )
            except requests.HTTPError as e:
                self.__write_json_db_to_disk()
                print(f"An error occurred: {e}. Restart application.")
                print(f"url: {article_url}")
            except requests.exceptions.RequestException as e:
                self.__write_json_db_to_disk()
                print(f"An error occurred: {e}. Restart application.")
                print(f"url: {article_url}")
            except TypeError as e:
                self.__write_json_db_to_disk()
                print(f"An error occurred: {e}. Restart application.")
                print(f"url: {article_url}")
            time.sleep(30)
        self.__write_json_db_to_disk()

    def __write_json_db_to_disk(self) -> None:
        """Write json db to disk."""
        with self.json_db_name.open("wb+") as json_file:
            json_file.write(orjson.dumps(self.json_db))

    def fire_request(self, article_url: str) -> None:
        """Fire request."""
        self.request: str = requests.get(
            article_url,
            headers=self.headers,
            timeout=10,
        ).text

    def make_soup(self) -> None:
        """Make soup."""
        self.soup: bs = bs(self.request, "lxml")

    def get_page_title(self) -> str:
        """Get page title.

        Returns:
            str: Page title.

        Raises:
            TypeError: If soup object is empty.

        """
        title_div: Tag | NavigableString | None = self.soup.find(
            "title"
        )
        if isinstance(title_div, Tag):
            return title_div.text.strip()
        message = "Title is is empty."
        raise TypeError(message)

    def get_page_authors(self) -> str:
        """Get page authors.

        Returns:
            str: Page authors.

        """
        authors_div: Tag | NavigableString | None = self.soup.find(
            "span", {"class": "author-name"}
        )
        if isinstance(authors_div, Tag):
            authors: str = authors_div.get_text(strip=True)
            return authors.lstrip("-")
        return ""

    def get_page_images(self) -> list[str]:
        """Get page images.

        Returns:
            list[str]: Page images.

        Raises:
            TypeError: If soup object is empty.

        """
        image_divs = list(self.soup.find_all("img"))
        if isinstance(image_divs, list):
            images: list[str] = [image_div.get("src") for image_div in image_divs]
            return images
        message = "Page images is empty."
        raise TypeError(message)

    def get_page_tags(self) -> list[str]:
        """Get page tags.

        Returns:
            list[str]: Page tags.

        """
        tags_div: Tag | NavigableString | None = self.soup.find(
            "div",
            {
                "class": "field field--name-field-tags field--type-entity-reference field--label-above"
            },
        )
        if isinstance(tags_div, Tag):
            tags: list[str] = [
                tag for tag in tags_div.get_text().split() if tag not in ["", "Tags"]
            ]
            return tags
        return []

    def get_article_body(self) -> str:
        """Get the article body.

        Returns:
            str: Article content.

        Raises:
            TypeError: If soup object is empty.

        """
        content_div: Tag | NavigableString | None = self.soup.find(
            "div",
            {
                "class": "clearfix text-formatted field field--name-body field--type-text-with-summary field--label-hidden field__item"
            },
        )
        if isinstance(content_div, Tag):
            return content_div.text.strip()
        message: str = "Article body is empty."
        raise TypeError(message)

    def get_published_date(self) -> str:
        """Get article content.

        Returns:
            str: Article content.

        Raises:
            TypeError: If soup object is empty.

        """
        date_div: Tag | NavigableString | None = self.soup.find()
        if isinstance(date_div, Tag):
            date_div.find("span", class_="authored-at is-pulled-right")
            return date_div.text.strip()
        message: str = "Soup object is empty."
        raise TypeError(message)

    def fetch_content(self, article_url: str) -> dict[str, str | list[str]]:
        """Fetch article content.

        Parameters
        ----------
        article_url : str
            Article url.

        Returns
        -------
        dict[str, str | list[str]]:
            Article content.

        """
        title: str = self.get_page_title()
        lang: str = str(detect(title)) if title else ""
        try:
            return {
                "url": article_url,
                "title": title,
                "published_date": self.get_published_date(),
                "authors": self.get_page_authors(),
                "language": lang,
                "tags": self.get_page_tags(),
                "images": self.get_page_images(),
                "categories": [],
                "article_content": self.get_article_body(),
            }
        except TypeError as e:
            print(article_url)
            print(e)
        return {}


if __name__ == "__main__":
    bodhi_snapshot = PageSnapShot()
