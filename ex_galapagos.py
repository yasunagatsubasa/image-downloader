#!python3

import csv
import argparse
import os

import requests
import bs4
from PIL import Image
import pandas as pd



def get_links(keywords, num):
    """
    Google検索から保存する画像のURLを取得する。
    httpsから始まるURLのみ取得する。

    Parameters
    ---
    keywords: list
        Google検索するクエリとなる文字列。
        半角スペースで区切られリストになっている。
    num: int
        保存する枚数。

    Returns
    ---
    links: list
        保存する画像のURLのリスト。
    """
    response = requests.get("https://www.google.com/search?q=" + "+".join(keywords) + "&tbm=isch")
    html = response.text
    soup = bs4.BeautifulSoup(html,'html.parser')
    links_all = soup.find_all("img")

    links = []
    cnt = 0
    for s in links_all:
        src = s.get("src")
        if src[:5] == "https":
            links.append(src)
            cnt += 1
            if cnt == num:
                break

    print("検索クエリ:", " ".join(keywords))
    print("取得予定枚数:", num)
    print("取得した枚数:", len(links))

    return links


def download_img(links, dir):
    """
    取得したURLから画像を保存する。

    Parameters
    ---
    links: list
        保存する画像のURLのリスト。
    dir: str
        ダウンロードした画像を保存するディレクトリ。

    Returns
    ---
    paths: list
        保存した画像ファイルのパスのリスト。
    """
    paths = []
    for i, link in enumerate(links):
        response = requests.get(link, stream=True)
        if response.status_code == 200:
            file_name = dir + "img{:02}".format(i)
            with open(file_name, 'wb') as f:
                f.write(response.content)
                print("saved:", file_name)
                paths.append(file_name)

    return paths


def save_csv(paths, csv_path):
    """
    保存した画像ファイルのフォーマットとサイズをCSVファイルに保存する。
    CSVには画像のパス、フォーマット、横幅、高さが記録される。

    Parameters
    ---
    paths: list
        保存した画像ファイルのパスのリスト。
    csv_path: str
        保存するCSVファイルのパス。
    """
    with open(csv_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['path', 'format', 'width', 'height'])
        for path in paths:
            img = Image.open(path)
            writer.writerow([path, img.format, img.width, img.height])


def process_img(paths, csv_path, dir):
    """
    ダウンロードした各画像に以下の処理をして保存する。
    1. グレーにする
    2. 反時計回りに90度回転させる

    Parameters
    ---
    paths: list
        保存した画像ファイルのパスのリスト。
    csv_path: str
        画像の情報が記載されたCSVファイルのパス。
    dir: str
        変換処理後のファイルを保存するディレクトリ。
    """
    df = pd.read_csv(csv_path)
    for path in paths:
        img = Image.open(path)

        img_gray = img.convert('L')
        img_rot = img_gray.rotate(90, expand=True)
        
        img_rot.save(dir + path.split('/')[-1] + '.' + df[df['path'] == path]['format'].iat[-1])



if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-k', '--keyword', required=True, nargs='*', type=str, help='この検索クエリでGoogle検索した画像を保存する. 半角スペース区切りで複数指定可能.')
    parser.add_argument('-d', '--dir', required=True, type=str, help='各ファイルを保存するディレクトリ名. 既存のディレクトリは指定できない.')
    parser.add_argument('-n', '--num', type=int, choices=list(range(1, 11)), default=1, help='何枚保存するか（1〜10枚）. default=1')
    parser.add_argument('-c', '--csv_filename', type=str, default='img_info', help='画像情報を格納するCSVファイルの名前. default=img_info')

    args = parser.parse_args()

    dir = args.dir + '/'

    if os.path.isdir(dir):
        print('既存のディレクトリは指定しないでください。')
    else:
        os.mkdir(dir)

        img_dir = dir + 'image/'
        result_dir = dir + 'result/'

        os.mkdir(img_dir)
        os.mkdir(result_dir)

        csv_path = dir + args.csv_filename + '.csv'

        links = get_links(args.keyword, args.num)
        paths = download_img(links, img_dir)
        save_csv(paths, csv_path)
        process_img(paths, csv_path, result_dir)
