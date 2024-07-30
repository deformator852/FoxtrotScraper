import sys
import scrapy
import json
import bs4


class FoxtrotSpider(scrapy.Spider):
    name = "foxtrot"
    start_url = "https://www.foxtrot.com.ua/uk/shop/mobilnye_telefony_smartfon.html"
    count_pages = 5
    data = []

    def start_requests(self):
        for page in range(1, self.count_pages):
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            }
            url = self.start_url + f"?page={page}"
            yield scrapy.Request(url=url, callback=self.parse, headers=headers)

    def parse(self, response, **kwargs):
        for card in response.css(".card__title"):
            link = card.css("a::attr(href)").get()
            absolute_link = response.urljoin(link)
            yield scrapy.Request(url=absolute_link, callback=self.parse_phone_detail)

    def parse_phone_detail(self, response):
        model = response.css("h1.page__title.overflow::text").get().strip()
        price = response.css("div.product-box__main_price::text").get().strip()
        grade = response.css("div.review-total-rating__value::text").get().strip()
        link = response.url
        phone_data = {"link": link, "price": price, "grade": grade, "feedback": []}
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        feedback_items = soup.find_all("div", class_="product-comment__item")
        for feedback in feedback_items:
            if feedback is not None:
                name = feedback.find(
                    "div", class_="product-comment__item-title"
                ).get_text(strip=True)
                grade = feedback.find(
                    "div", class_="product-comment__item-rating"
                ).get_text(strip=True)
                message = feedback.find(
                    "div", class_="product-comment__item-text"
                ).get_text(strip=True)
                if (
                    len(grade) > 1
                ):  # len(grade) > 1 here because if feedback have no grade so that's question and we should skip it
                    phone_data["feedback"].append(
                        {
                            "name": name,
                            "grade": grade,
                            "message": message,
                        }
                    )
        self.data.append({model: phone_data})

    def closed(self, reason):
        with open("phones.json", "w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)
