import os, re, time, shutil
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool

temp = './temp/'

def get_site(url):
    response = requests.get(url)
    html = BeautifulSoup(response.content, 'html.parser')
    response.close()

    return html

def scrape(data_list):
    html = get_site(data_list[1])

    try:
        content = html.find(id='chapter').find_all('p')
    except:
        content = html.find(id='chapter-content').find_all('p')

    content = [ x.get_text() for x in content ]
    content = [ x.strip() for x in content ]
    content = [ x + '\n\n' for x in content ]
    content = ''.join(content)

    with open(temp + data_list[0] + '.txt', 'w', encoding='utf-8') as target:
        target.write(content)
        target.close()

    print('    Acquired: ' + data_list[0], end='\r')

def search_dots(n):
    dots = {
        0:'       ',
        1:'    .  ',
        2:'    .. ',
        3:'    ...'
    }

    print(dots.get(n), end='\r')

def main():
    url = input('input url: ')

    start_time = time.time()

    html = get_site(url)

    novel_title = html.find(class_='title').get_text()
    print('\n    Novel title: {}'.format(novel_title))

    novel_author = html.find(class_='info').find_all('div')[0].get_text().split(',')
    novel_author = novel_author[0][7:]
    print('    Novel author: {}'.format(novel_author))

    main_url = url.split('/')[0:3]
    main_url = '/'.join(main_url)

    url_list = []

    n = 0

    while True:
        search_dots(n)

        html = get_site(url)

        columns = html.find_all(class_='list-chapter')

        for column in columns:
            rows = column.find_all('a')
            for row in rows:
                url_list.append(main_url + row.get('href'))

        try:
            url = main_url + html.find(class_='next').find('a').get('href')

            if n < 3:
                n += 1
            else:
                n = 0

        except:
            break

    print('    Chapters: {}'.format(len(url_list)))

    try:
        os.mkdir(temp)
    except:
        pass

    name_list = []

    for x in range(len(url_list)):
        x = 'ch' + '{}'.format(x + 1).zfill(4)

        name_list.append(x)

    data_list = set(zip(name_list, url_list))

    with Pool(10) as pool:
        crawler = pool.map(scrape, data_list)

    temp_files = os.listdir(temp)

    print('    Acquired: ' + str(len(temp_files)) + ' files', end='\r')

    # made by @Toothy with a comment on https://nedbatchelder.com/blog/200712/human_sorting.html post
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    temp_files.sort(key=alphanum_key)

    with open(novel_title + '.txt', 'w', encoding='utf-8') as f1:
        f1.write('Novel title: {}\nNovel author: {}\nChapters: {}'.format(novel_title, novel_author, len(url_list)))

        print('    Merged:             ', end='\r')

        for chapter in temp_files:
            print('    Merged: ' + chapter, end='\r')

            with open(temp + chapter, encoding='utf-8') as f2:
                for line in f2:
                    f1.write(line)

    stop_time = time.time()

    shutil.rmtree(temp)

    print('    Done in {:.2f}s    '.format(stop_time - start_time))

if __name__ == '__main__':
    main()
