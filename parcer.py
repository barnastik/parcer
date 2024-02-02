import scrapy
from scrapy.http import Request
from scrapy.item import Item, Field


class FilmItem(Item):
    Название = Field()
    Жанр = Field()
    Режиссёр = Field()
    Страна = Field()
    Год_выпуска = Field()


class FilmsSpider(scrapy.Spider):
    name = 'films'
    start_urls = ['https://ru.wikipedia.org/wiki/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%A4%D0%B8%D0%BB%D1%8C%D0%BC%D1%8B_%D0%BF%D0%BE_%D0%B0%D0%BB%D1%84%D0%B0%D0%B2%D0%B8%D1%82%D1%83']

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'films_data.csv',
        'CLOSESPIDER_ITEMCOUNT': 0
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        for film in response.css('div.mw-category-group ul li'):
            film_link = response.urljoin(film.css('a ::attr(href)').get())
            yield scrapy.Request(film_link, callback=self.parse_film_page, meta={'film_name': film.css('a ::text').get()})

        next_page_link = response.css('a:contains("Следующая страница")::attr(href)').get()
        if next_page_link:
            yield scrapy.Request(response.urljoin(next_page_link), callback=self.parse)

    def parse_film_page(self, response):
        film_info = {'Название': response.meta['film_name']}
        
        film_name = response.meta['film_name']
        if film_name.strip() == 'Телефильмы по алфавиту' or film_name.strip() == 'Мультфильмы по алфавиту':
            return

        rows = response.css('table.infobox tbody tr')
        for row in rows:
            label = row.css('th::text').get()
            if label:
                label = label.strip()
            if label in ['Жанр', 'Режиссёр', 'Страна', 'Год']:
                value = row.css('td *::text').getall()
                value = [v.strip() for v in value if v.strip()]
                if label == 'Год':
                    label = 'Год_выпуска'
                if value:
                    film_info[label] = ", ".join(value)
        #genres = response.css('th:contains("Жанр")::text, th:contains("Жанр") + td a::text, th:contains("Жанры") + td span::text, th a[title^="Жанры"] + td span::text').getall()
        #film_info['Жанр'] = ', '.join(genres) if any(genres) else ''

        genres = response.css('th:contains("Жанр")::text, th:contains("Жанр") + td a::text, th:contains("Жанры") + td span::text, th a[title^="Жанры"] + td span::text').getall()
        genres = [genre.strip() for genre in genres if genre.strip()]
        film_info['Жанр'] = ', '.join(genres)

        film_item = FilmItem(film_info)
        yield film_item
