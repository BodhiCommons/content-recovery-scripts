import requests
import time
import json
import os
from bs4 import BeautifulSoup
from langdetect import detect

def download_and_process_image(image_url):
    url = "https://web.archive.org" +image_url
    base_dir='images'
    os.makedirs(base_dir, exist_ok=True)

    save_path=os.path.join(base_dir,url.split('/')[-1])
    try:
        # Send a GET request to the image URL
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful

        # Open a file in binary write mode and save the image
        with open(save_path, 'wb') as file:
            file.write(response.content)

        print(f"Image successfully downloaded and saved to {save_path}")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")


class WebScraper:
    def __init__(self, url):
        self.url = url
        self.soup = None

    # Method to fetch the webpage
    def fetch_page(self):
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                print("Page fetched successfully.")
                self.soup = BeautifulSoup(response.content, 'html.parser')
        except:
            print("Fetching failed")
    
    # Method to extract the page title
    def get_page_title(self):
        if self.soup:
            title_div = self.soup.find('title')
            print(title_div)
            if title_div:
                title=title_div.get_text()
                return title
        else:
            raise Exception("Soup object title is empty.")
        return None

    # Method to extract the authors
    def get_page_authors(self):
        if self.soup:
            authors_div = self.soup.find('span', {'class': 'author-name'})
            if authors_div:
                authors= authors_div.get_text(strip=True)
                return authors.lstrip('-')
        else:
            raise Exception("Soup object authors is empty.")
        return None

    def get_page_images(self):
        if self.soup:
            image_div =self.soup.find_all('img')
            if image_div:
                images=[img.get('src') for img in image_div]
                return images
        return None


    # Method to extract the page tags
    def get_page_tags(self):
        if self.soup:
            tags_div = self.soup.find('div', {'class': 'field field--name-field-tags field--type-entity-reference field--label-above'})
            if tags_div:
                tags=[tag for tag in tags_div.get_text().split() if tag not in ['','Tags']]
                return tags
        else:
            raise Exception("Soup object tags is empty.")
        return None


    # Method to extract main content (assuming it is inside a div with a specific class)
    def get_article_content(self):
        if self.soup:
            content_div = self.soup.find('div', {'class': 'clearfix text-formatted field field--name-body field--type-text-with-summary field--label-hidden field__item'})  
            if content_div:
                content_text = content_div.get_text(separator="\n", strip=True)
                return content_text
            else:
                return None
        else:
            raise Exception("Soup object is empty. Fetch the page first.")
        return None

    # Method to print all extracted content
    def fetch_content(self):
        try:
            title=self.get_page_title()
            lang=detect(title) if title else None
            
            content={
                    "url":self.url,
                    "title": title,
                    "authors": self.get_page_authors(),
                    "language": lang,
                    "tags":  self.get_page_tags(),
                    "images":self.get_page_images(),
                    "categories": None,
                    "article_content":self.get_article_content(),
                    "full_html":str(self.soup)
                    }
            return content
        except Exception as e:
            print(e)
        return None


# Usage example
if __name__ == "__main__":
    # URL to scrape
    url = "https://web.archive.org/web/20230127184806/http://bodhicommons.org/discontents_within_syro_malabar_church_kerala"
    url_list=[]
    for fn in os.listdir('urls'):
        with open(os.path.join("urls",fn)) as fp:
            data=fp.read()
        url_list.extend(data.strip().split("\n"))
        
    i=0
    full_content=[]
    image_dict={}
    image_list=[]
    failed_urls=[]
    for url in list(set(url_list)):
        time.sleep(30) 
        # Create an instance of WebScraper
        scraper = WebScraper(url)

        # Fetch page, and print the content
        scraper.fetch_page()  # Fetch the HTML content
        content=scraper.fetch_content()  # fetch title and content and other details
        if content ==None or content["title"]==None:
            failed_urls.append(url)
        else:
            full_content.append(content)
            if content['images'] is not None:
                image_list.extend(content['images'])
            print(content['title'])
        i+=1
    json.dumps(full_content)

    # Store JSON to a file
    with open('bodhi_data.json', 'w', encoding='utf-8') as file:
        json.dump(full_content, file, ensure_ascii=False, indent=4)  

    print("JSON data has been stored in bodhi_data.json")


    for image_url in list(set(image_list)):
        download_and_process_image(image_url)



