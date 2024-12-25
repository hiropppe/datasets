import argparse
import httpx
import os
import random
import re
import sys
import time
import traceback

from lxml import html


headers = {}
cookies = {'age_check': '1'}

toxicity_genres = (333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 378, 379, 381)

timeout = httpx.Timeout(10.0, connect=30.0)


def main(dest, dryrun, genres):
    os.makedirs(dest, exist_ok=True)

    genre_page = http_get('https://blog.fc2.com/genrelist/')
    genre_anchor_nodes = html.fromstring(genre_page.text).xpath('//*[@class="subgenre_name_list"]/li/a')
    genre_list = [(''.join(node.itertext()).strip(), node.attrib['href']) for node in genre_anchor_nodes]

    for name, url in genre_list:
        url = to_absolute_url(url)
        genre_id = re.findall(r'subgenre/([0-9]+)/', url)[0]
        genre_dest = os.path.join(dest, genre_id)

        if genres and genre_id not in genres.strip().split(','):
            continue

        print(f'{name}: {url}')
        try:
            scraping_genre(url, genre_dest, dryrun=dryrun)
        except KeyboardInterrupt:
            break


def scraping_genre(url, genre_dest, dryrun=False):
    os.makedirs(genre_dest, exist_ok=True)
    while True:
        page = None
        try:
            page = http_get(url)
            entry_urls = list(set(re.findall(r'https?://.+fc2.com/blog-entry-.+\.html', page.text)))
            for entry_url in entry_urls:
                try:
                    download_html(entry_url, genre_dest, dryrun=dryrun)
                    if not dryrun:
                        time.sleep(random.random()) 
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    print(f"{type(exc).__name__}. {str(exc)} {entry_url}", file=sys.stderr)
                    with open('./errors', 'a') as f:
                        print(entry_url, file=f)
        finally:
            if page:
                url = get_next_page(page.text)
                if url:
                    print(url)
                else:
                    print('EOP', file=sys.stderr)
                    break


def http_get(url):
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()
        return response


def get_next_page(html_text):
    pager_anchor_nodes = html.fromstring(html_text).xpath('//*[@class="pager"]/a')
    next_page = [node.attrib['href'] for node in pager_anchor_nodes if node.text == '>']
    if len(next_page) == 1:
        return to_absolute_url(next_page[0])


def download_html(url, genre_dest, dryrun=False):
    server, entry = url.split('/')[-2:]
    save_file = f"{server}#{entry}"
    save_path = os.path.join(genre_dest, save_file)
    print(f'{url} -> {save_path}')
    if not dryrun:
        with open(save_path, 'w') as f:
            text = http_get(url).text
            if len(text.encode()) <= 10240:
                raise Exception(f"Too small content text ({len(text.encode())} bytes). '{text}'")
            print(text, file=f)


def to_absolute_url(url):
    # adult categories
    if url.startswith('//blog.fc2.com/a/'):
        url = f'https:{url}'
    else:
        url = f'https://blog.fc2.com{url}'
    return url


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FC2 Blog Scraper.')
    parser.add_argument('--dest', '-d', default='/data/fc2b/html')
    parser.add_argument('--dryrun', action='store_true')
    parser.add_argument('--genres')

    args = parser.parse_args()

    main(args.dest, args.dryrun, args.genres)
