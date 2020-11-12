import os, re, time, shutil
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool

# the only global variable, would be nice if i could somehow implement it in
# main() but idk how?
temp = './temp/'

# gets the url and returns beautifulsoup'd html
#
# it's used multiple times so i decided that it was maybe smarter to make it a
# separate function?
def get_site(url):
    # uses requests to get the website
    response = requests.get(url)
    # formats the website response
    html = BeautifulSoup(response.content, 'html.parser')
    # closes the website request - maybe unnecessary?
    response.close()

    # returns the beautifulsoup'd html
    return html

def scrape(data_list):
    # get's beautifulsoup'd html usint the url provide by the data_list
    html = get_site(data_list[1])

    # some chapters are in the chapter thing others in the chapter-content thing
    # this tries the chapter thing first and if it raises and exception it tries
    # the chapter-content thing
    #
    # the definition of a quick and dirty fix, i wonder if there is a better
    # way to do this?
    try:
        # creates a list containg all paragraphs in in the chapter thing
        # inside the html acquired above
        content = html.find(id='chapter').find_all('p')
    except:
        # creates a list containg all paragraphs in the chapter-content thing
        # inside the html acquired above
        content = html.find(id='chapter-content').find_all('p')

    # get's the text from the paragraph in the content list
    content = [ x.get_text() for x in content ]
    # removes all the spaces surrounding the text to fix weird site formatting
    content = [ x.strip() for x in content ]
    # adds a line break after each paragraph
    content = [ x + '\n\n' for x in content ]
    # joins the content list into a large string
    content = ''.join(content)

    # creates a new file using the name provided by the data_list
    with open(temp + data_list[0] + '.txt', 'w', encoding='utf-8') as target:
        # writes the content string inside the file
        target.write(content)
        # closes the file
        target.close()

    # prints which chapter the function acquired
    print('    Acquired: ' + data_list[0], end='\r')

# displays strings depending on the number n, pretty much eye candy used to
# show that the script is running while it's gathering chapter urls
#
# smart usage of the dictionary maybe?
def search_dots(n):
    dots = {
        0:'       ',
        1:'    .  ',
        2:'    .. ',
        3:'    ...'
    }

    print(dots.get(n), end='\r')

# main function
def main():
    # get's the ToC link
    url = input('input url: ')

    # defines the script start time
    start_time = time.time()

    # get's the website html
    html = get_site(url)

    # finds the novel title
    novel_title = html.find(class_='title').get_text()
    print('\n    Novel title: {}'.format(novel_title))

    # finds the novel author
    novel_author = html.find(class_='info').find_all('div')[0].get_text().split(',')
    novel_author = novel_author[0][7:]
    print('    Novel author: {}'.format(novel_author))

    # TODO: get other novel data such as the genre, the source, and
    # maybe if it's completed or not...

    # formats the given url to get the base url for future use
    # https://novelfull.com/dimensional-sovereign.html -> https://novelfull.com
    # notice it doesn't have the slash at the end...
    main_url = url.split('/')[0:3]
    main_url = '/'.join(main_url)

    # created an empty list for formated chapter links
    url_list = []

    # value used by the search_dots() function
    n = 0

    # simple loop that a) get's the page html again (i could maybe skip this
    # part but idk how i would implement it otherwise), b) finds the chapter urls
    # on the page, and scrapes them before finding the next page url, and
    # repeating the steps until it get's to the last page
    while True:
        # eye candy
        search_dots(n)

        # as before, get's beautifulsoup'd html
        html = get_site(url)

        # finds and formats chapter links before appending them to the url_list
        columns = html.find_all(class_='list-chapter')

        for column in columns:
            rows = column.find_all('a')
            for row in rows:
                url_list.append(main_url + row.get('href'))

        # try's to find the next page link
        # if it succeeds it changes the url used and adds +1 to the value n
        # which is used for eye candy
        try:
            # formats the next page url using the main_url defined earlier
            url = main_url + html.find(class_='next').find('a').get('href')

            # checks n value, and depending on the condition it either resets
            # it to 0 or gives it +1 (used for eye candy)
            if n < 3:
                n += 1
            else:
                n = 0

        except:
            # in case there is no next page url the loop is broken
            break

    # prints the amount of chapter links gathered
    print('    Chapters: {}'.format(len(url_list)))

    # tries to make a folder to store scraped chapters
    # try is used to prevent the script raising an exception if for some reason
    # the folder is already present
    try:
        # creates a temp folder
        os.mkdir(temp)
    except:
        # if folder is present, pass without raising and exception
        pass

    # creates an empty list for scraped chapter names
    name_list = []

    # creates numbered names for all scraped chapters
    for x in range(len(url_list)):
        # creates the numbered name
        x = 'ch' + '{}'.format(x + 1).zfill(4)
        # appends the name to the name_list
        name_list.append(x)

    # creates a data_list combining the name_list with the url_list
    # [[name, url], [name, url]...] <- data_list format
    data_list = set(zip(name_list, url_list))

    # the easiest way that i found to implement multiprocessing for a
    # simple web-scraper idk what else to say?
    with Pool(10) as pool:
        # defies the "crawler" (bs) and creates separate processes for the
        # scrape function feeding it the data_list
        crawler = pool.map(scrape, data_list)

    # prototype web-scraping code used before i had to make it a function
    # to implement multiprocessing ("...")
    #
    # for i, url in enumerate(url_list):
    #     i = 'ch' + '{}'.format(i + 1).zfill(4)
    #
    #     html = get_site(url)
    #
    #     content = html.find(id = 'chapter-content').find_all('p')
    #     content = [ x.get_text() for x in content ]
    #     content = [ x + '\n\n' for x in content]
    #     content = ''.join(content)
    #
    #     with open(temp + i + '.txt', 'w', encoding='utf-8') as target:
    #         target.write(content)
    #         target.close()
    #
    #     print('    Acquired: ' + i, end='\r')

    # checks the temporary folder, get's all file name and puts them in a
    # temp_files list
    temp_files = os.listdir(temp)

    # prints the amount of chapters acquired using the len() of the temp_files
    # list. it's a simple way to allow the user to see if the amount of
    # chapters that were downloaded matches the amount of chapters there is
    print('    Acquired: ' + str(len(temp_files)) + ' files', end='\r')

    # relic that is left from when i used to name the chapters "1, 2, 3...",
    # and is used to fix the "weird" sorting thing. now i keep it as a precaution
    #
    # made by @Toothy with a comment on https://nedbatchelder.com/blog/200712/human_sorting.html post
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    temp_files.sort(key=alphanum_key)

    # creates the main novel file and names it using the novel_title
    with open(novel_title + '.txt', 'w', encoding='utf-8') as f1:
        # inside the file it writes the novel data
        f1.write('Novel title: {}\nNovel author: {}\nChapters: {}'.format(novel_title, novel_author, len(url_list)))
        # clears the acquired string printed above
        print('    Merged:             ', end='\r')
        # for each file (chapter) in the temp_files list
        for chapter in temp_files:
            # prints file name (chapter)
            print('    Merged: ' + chapter, end='\r')
            # opens a file from the temporary filder
            with open(temp + chapter, encoding='utf-8') as f2:
                # reads line by line in the file from the temporary folder
                for line in f2:
                    # writes the read line to the main novel file
                    f1.write(line)

    # defines the script end time
    stop_time = time.time()

    # removes the temporary folder (including the individual chapters within)
    shutil.rmtree(temp)

    # prints the time the script was getting the novel
    print('    Done in {:.2f}s    '.format(stop_time - start_time))

# if i understand correctly this prevents the code running if it's imported
if __name__ == '__main__':
    main()
