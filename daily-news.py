import requests
from bs4 import BeautifulSoup
from telegram import Bot
import schedule
import time
import logging
from datetime import datetime
import os
import json

logging.basicConfig(filename='news_bot.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


TELEGRAM_TOKEN = '' // change here
CHAT_ID = '' // change here

bot = Bot(token=TELEGRAM_TOKEN)

LAST_RUN_FILE_HN = 'the_hacker_news.json'
LAST_RUN_FILE_BP = 'bleeping_computer.json'

data_atual = datetime.now().strftime('%b %d, %Y')


def fetch_the_hacker_news():
    """
    Realizara o scrapping no site do the hacker news
    ira retornar uma lista contendo um dicionario dentro
    """

    noticias_novas = []
    noticias = []
    noticias_salvas = []
    if os.path.exists(LAST_RUN_FILE_HN):
        with open(LAST_RUN_FILE_HN, 'r', encoding='utf-8') as f:
            noticias_salvas = json.load(f)
    
    the_hacker_news_url = "https://thehackernews.com/"

    logging.info("Fetching news for %s", the_hacker_news_url)

    response = requests.get(the_hacker_news_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    blog_posts = soup.find('div', class_="blog-posts clear")
    posts = blog_posts.find_all("div", class_="body-post clear")
    for post in posts:

        news_title = post.find('h2', class_="home-title").text

        news_date = post.find("span", class_="h-datetime")
        news_date.i.extract()
        news_date = news_date.text.strip()

        news_link_tag = post.find("a", class_="story-link")
        news_link = news_link_tag['href']
        
        if news_date == data_atual:
            noticia_atual = {"titulo": news_title, 'data': news_date, 'link': news_link}
            noticias.append(noticia_atual)
            if not any(noticia_salva['titulo'] == noticia_atual['titulo'] for noticia_salva in noticias_salvas):
                noticias_novas.append(noticia_atual)

    noticias_salvas.extend(noticias_novas)

    with open(LAST_RUN_FILE_HN, 'w', encoding='utf-8') as f:
        json.dump(noticias_salvas, f, ensure_ascii=False, indent=4)
    
    if noticias_novas:
        return noticias_novas
    
    else:
        return None


def fetch_bleeping_computer():
    """
    Realizara o scrapping no site do bleeping computer
    ira retornar uma lista contendo um dicionario dentro
    """
    data_atual = datetime.now().strftime('%B %d, %Y')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    noticias_novas = []
    noticias = []
    noticias_salvas = []

    if os.path.exists(LAST_RUN_FILE_BP):
        with open(LAST_RUN_FILE_BP, 'r', encoding='utf-8') as f:
            noticias_salvas = json.load(f)

    url = "https://www.bleepingcomputer.com/"

    logging.info("Fetching news for %s", url)

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    blog_posts = soup.find('section', class_="bc_main_content")
    if not blog_posts:
        logging.error("Section with class 'bc_main_content' not found.")
        return None

    posts = blog_posts.find_all('li')
    for post in posts:

        h4_tag = post.find('h4')
        if h4_tag:
            news_title = h4_tag.get_text(strip=True)
        else:
            logging.warning("No <h4> tag found in this <li> element.")
            continue

        news_date_tag = post.find("li", class_="bc_news_date")
        if news_date_tag:
            news_date = news_date_tag.get_text(strip=True)
        else:
            logging.warning("No date found in this <li> element.")
            continue
        
        news_link_tag = h4_tag.find('a') if h4_tag else None
        if news_link_tag:
            news_link = news_link_tag['href']
        else:
            logging.warning("No <a> tag found within <h4> tag.")
            continue
       
        if news_date == data_atual:
            noticia_atual = {"titulo": news_title, 'data': news_date, 'link': news_link}
            noticias.append(noticia_atual)
            if not any(noticia_salva['titulo'] == noticia_atual['titulo'] for noticia_salva in noticias_salvas):
                noticias_novas.append(noticia_atual)

    noticias_salvas.extend(noticias_novas)

    with open(LAST_RUN_FILE_BP, 'w', encoding='utf-8') as f:
        json.dump(noticias_salvas, f, ensure_ascii=False, indent=4)
    
    if noticias_novas:
        return noticias_novas
    else:
        return None

def formatar_mensagem_markdown(noticias, fonte):
    mensagem = f"*{fonte} Updates:*"
    for noticia in noticias:
        titulo = noticia['titulo']
        data = noticia['data']
        link = noticia['link']
        mensagem += f"\n\n*{titulo}*\n_{data}_\n[Leia mais]({link})"
    return mensagem


def enviar_mensagem_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': mensagem,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    logging.info("Mensagem enviada.")

def main():
    logging.info("Job started")

    the_hacker_news = fetch_the_hacker_news()

    if the_hacker_news:
        mensagem = formatar_mensagem_markdown(the_hacker_news, "The Hacker News")
        enviar_mensagem_telegram(mensagem)
    else:
        logging.info("Nenhuma noticia nova no The Hacker News")

    bleeping_computer = fetch_bleeping_computer()

    if bleeping_computer:
        mensagem = formatar_mensagem_markdown(bleeping_computer, "Bleeping Computer")
        enviar_mensagem_telegram(mensagem)
    else:
        logging.info("Nenhuma noticia nova no Bleeping Computer")


if __name__ == "__main__":
    main()
