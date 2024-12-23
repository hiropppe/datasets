import argparse
import glob
import json
import lxml
import os
import re
import httpx
import sys

from readability.readability import Document
from tqdm import tqdm


toxicity_genres = ('333', '334', '335', '336', '337', '338', '339', '340', '341', '342', '343', '344', '345', '378', '379', '381')


def main(source, output):
    data = []
    sub2X = get_sub2X_map()
    for path in tqdm(glob.glob(os.path.join(source, '**/*.html'), recursive=True)):
        blog, entry = path.split('/')[-1].split('#')
        subgenre_id = path.split('/')[-2]
        toxicity = 1 if subgenre_id in toxicity_genres else 0
        try:
            title, summary = readability(open(path).read())
            if summary.strip():
                data.append({
                    'blog': blog,
                    'entry': entry,
                    'genre_id': sub2X[subgenre_id][0],
                    'genre_name': sub2X[subgenre_id][1],
                    'subgenre_id': subgenre_id,
                    'subgenre_name': sub2X[subgenre_id][2],
                    'toxicity': toxicity,
                    'title': title,
                    'text': summary
                })
        except Exception as exc:
            print(f"{type(exc).__name__}. {str(exc)} {path}", file=sys.stderr)

    with open(output, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=True)


def get_sub2X_map():
    genre_list = httpx.get('https://blog.fc2.com/genrelist/')
    genre_groups = lxml.html.fromstring(genre_list.text).xpath('//*[@class="genre_group"]')
    genre_dict = []
    for group in genre_groups:
        genre = group.xpath('./h3/a')[0]
        genre_id = genre.attrib['href'].strip().split('/')[-2]
        genre_text = genre.text.strip()
    
        children = []
        subgenres = group.xpath('./ul/li/a')
        for node in subgenres:
            subgenre_id = re.findall(r'/subgenre/([0-9]+)/', node.attrib['href'])[0]
            subgenre_text = ''.join(node.itertext()).strip()
            children.append({
                'id': subgenre_id,
                'name': subgenre_text
            })

        genre_dict.append({
            'id': genre_id,
            'name': genre_text,
            'subgenre': children
        })
    
    sub2X = {subgenre['id']: (genre['id'], genre['name'], subgenre['name']) for genre in genre_dict for subgenre in genre['subgenre']}
    return sub2X

def readability(html):
    doc = Document(html)
    title = doc.title()
    summary = doc.summary()
    summary_text = lxml.html.fromstring(summary).text_content().strip()
    return title, summary_text


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
