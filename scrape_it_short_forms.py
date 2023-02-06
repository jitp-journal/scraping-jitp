# import necessary packages for webscraping.

from dataclasses import replace
from bs4 import BeautifulSoup
from urllib import request
from dateutil.parser import parse
import time
import random
import os
import re
import csv

def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

def get_issue_link(link):
    html = request.urlopen(link).read()
    soup = BeautifulSoup(html, 'html5lib')
    issue_toc = soup.select('div.textcontent')[0]
    raw_links = issue_toc.find_all('a')
    actual_issue_links = []
    for raw_link in raw_links:
        if raw_link.text.startswith('Issue') or raw_link['href'].startswith('https://jitp.commons.gc.cuny.edu/wp-content/plugins/peters-custom-anti-spam-image/custom_anti_spam.php') or raw_link['href'].startswith('https://jitp.commons.gc.cuny.edu/a-conversation-on-international-collaboration-in-digital-scholarship/'):
            pass
        elif raw_link.has_attr("title") and raw_link['title'] == "Share this article":
            pass
        elif raw_link['href'].endswith('#respond') or raw_link['href'].endswith('#comments') or '#comment' in raw_link['href']:
            pass
        elif raw_link.text in ['Attribution-NonCommercial-ShareAlike 4.0 International', 'Previous:', 'Next:', 'Learn how your comment data is processed', 'table of contents', 'Introduction /', 'JITP Issue 8 is now live! | Laura Wildemann Kane','JITP Issue 9 is now live! | Laura Wildemann Kane','Happenings – VREPS','Re-viewing Digital Technologies and Art History – DAHS','Wandering Volunteer Park /', '\n', 'Special Feature: Behind the Seams', 'Summer Supplement: A Conversation on International Collaboration in Digital Scholarship', 'Manifold']:
            pass
        elif raw_link['href'] in ['https://creativecommons.org/licenses/by-nc-sa/4.0/', 'http://teacherstech.net/?p=10236']:
            pass
        elif is_date(raw_link.text):
            pass
        elif raw_link.text in [text.replace(u'\xa0', u'') for link, text in actual_issue_links]:
            pass
        else:
            actual_issue_links.append((raw_link['href'], raw_link.text.replace(u'\xa0', u'')))
    
    return actual_issue_links

def scrape_contents_of_an_article(article_link):
    html = request.urlopen(article_link).read()
    soup = BeautifulSoup(html, 'html5lib')
    # swap this line and the following one to grab only the article and not the comments
    # issue_contents = soup.select('article')[0]
    issue_contents = soup.select('div#main')[0]
    # add 'li.a[href$="#comments' to get rid of comments
    list_of_junk = ['div.tagslist','div.iw-social-share','a[href^="https://jitp.commons.gc.cuny.edu/category/issues"]', 'section#post-nav', 'div.comment-respond','p.akismet_comment_form_privacy_notice', 'p[style="display: none !important;"]', 'section.comments p.buttons', 'section.comments img', 'img.avatar', 'div.featimg.animated', 'div.cat']
    for junk in list_of_junk:
        # print(junk)
        try:
            issue_contents.select(junk)[0].decompose()
        except:
            pass
            # print('could not match ' + junk)
        try:
            for item in issue_contents.select(junk):
                item.decompose()
        except:
            print('not a thing we can loop over')
    # massaging of author bios
    try:
        for quote in issue_contents.find_all('blockquote'):
            try:
                if quote.h3.text == "About the Authors" or quote.h3.text == "About the Author":
                    quote.name = 'div'
                    quote['id']='authorbio'
                try:
                    quote.h3.name = 'h2'
                except:
                    pass
            except:
                pass

            try:
                if quote.h2.text == "About the Authors" or quote.h2.text == "About the Author":
                    try:
                        quote.name = 'div'
                        quote['id']='authorbio'
                    except:
                        pass
            except:
                pass
    except:
        pass

    #turn all address tags into p
    try:
        for address in issue_contents.find_all('address'):
            address.name = 'p'
    except:
        pass

    # remove bold from h2
    try:
        for abstract in issue_contents.find_all('h2'):
            if address.b:
                address.b.unwrap()
    except:
        pass
    # make all h3 abstracts into h2
    try:
        for h3 in issue_contents.find_all('h3'):
            if h3.text == "Abstract":
                h3.name = 'h2'
    except:
        pass
     # get rid of comment links and reformat date to not be a line item
    try:
        pass
        replace_text = issue_contents.select('ul.textinfo')[0].find_all('li')[1].text.strip()
        # replace_text = '<p>' + replace_text + '</p>'
        # replace_text = BeautifulSoup(replace_text)
        issue_contents.select('ul.textinfo')[0].replace_with(replace_text)
        # text_info = issue_contents.select('ul.textinfo')[0].find_all('li')
        # # text_info[0].decompose()
        # text_info.contents = text_info[1].text
    except:
        pass
    # search for image tags and replace direct links

    for img in issue_contents.find_all('img'):
        img['src'] = re.sub(
        r'https:\/\/jitp\.commons\.gc\.cuny\.edu\/files\/[0-9]+\/[0-9]+|src="http:\/`\/jitp\.commons\.gc\.cuny\.edu\/files\/[0-9]+\/[0-9]+|https:\/\/jitp\.commons\.gc\.cuny\.edu\/files\/EasyRotatorStorage\/user\-content\/erc\_62\_1406481274\/content\/assets',"images", img['src'])
        del img['srcset']

    for sup_tag in issue_contents.find_all("sup", {"class": "footnote"}):
        del sup_tag.findChild('a')['onclick']
    
    # setting the byline tag
    print(article_link)
    try:
        for hit in issue_contents.find_all('h2', {"class": 'byline'}):
            hit.name = 'p'
    except:
        # if no h2 with byline - just pass
        # but issue right now is that sometimes there is no byline class but there is an h2. you could say "turn the first h2 into a p tag, but you won't know universally that is the case"
        print('Fail: ' + article_link)
        pass
    try:
        for thing in issue_contents.select('a[href^="https://jitp.commons.gc.cuny.edu/files"]'):
            thing.replaceWithChildren()
    except:
        pass
    try:
        for thing in issue_contents.select('a[href^="http://jitp.commons.gc.cuny.edu/files"]'):
            thing.replaceWithChildren()
    except:
        pass
    # strip brackets from notes
    for hit in issue_contents.find_all('a', {'class': 'ftn'}):
        hit.string.replace_with(re.sub('[\[\]]', '', hit.string))
    for hit in issue_contents.find_all('a', {'class': 'ftnref'}):
        hit.string.replace_with(re.sub('[\[\]]', '', hit.string))
    return issue_contents

def clean_issue(title, issue_contents):
    metadata_title = "<head>\n<meta name=\"dc.title\" content=\"" + title + "\">\n</head>"
    clean_contents = metadata_title + str(issue_contents)
    # re.sub(
    #     r'img src="https:\/\/jitp\.commons\.gc\.cuny\.edu\/files\/[0-9]+\/[0-9]+|src="http:\/\/jitp\.commons\.gc\.cuny\.edu\/files\/[0-9]+\/[0-9]+',"<img src=\"images", clean_contents)
    
    return clean_contents

def scrape_issue(issue_title,issue_links):
    if not os.path.exists(issue_title):
        os.mkdir(issue_title)
    print('Processing ' + issue_title)
    print(issue_links)
    for link,title in issue_links:
        print(title)
        contents = scrape_contents_of_an_article(link)
        clean_contents = clean_issue(title, contents)
        with open(os.path.join(issue_title, title.replace('/', ' ') +'.html'), 'w') as fout:
            fout.write(clean_contents)


def get_main_toc_links():
    # store the url we want to work with in the variable 'url'

    url = 'https://jitp.commons.gc.cuny.edu/issues/'
    html = request.urlopen(url).read()

    # turn it into soup
    soup = BeautifulSoup(html, 'html5lib')
    # grab just the toc from the page
    toc = soup.select('div.textcontent')[0]
    # grab all the anchor tags from the toc but throw away the ones about cc lincensing
    raw_links = toc.find_all('a')[1:-2]
    actual_links = [(raw_link['href'], raw_link.text.replace(u'\xa0', u' ').replace('Table of Contents: ','')) for raw_link in raw_links]
    return actual_links

def get_all_issue_links(main_toc_links):
    links_for_individual_issues = {}
    # MODIFY HERE TO REDUCE NUMBER OF ISSUES SCRAPED
    for issue_toc_link, issue_title in main_toc_links:
        if issue_title in ['Manifold', 'Issue Twenty-One', 'Summer Supplement: A Conversation on International Collaboration in Digital Scholarship']:
            pass
        else:
            max_sleep = 5
            time.sleep(random.random() * max_sleep)
            print('=====')
            print('Scraping ' + issue_title)
            links_for_individual_issues[issue_title] = get_issue_link(issue_toc_link)
    
    return links_for_individual_issues

def main():
    # get all the main toc links
    # main_toc_links = get_main_toc_links()
    # main_toc_links.reverse()



    # use the main toc links to get each issue link
    links_for_individual_short_forms= {'tool tips':[], 'teaching fails':[],'reviews':[], 'blueprints':[], 'assignments':[], 'behind the seams':[]}
    with open('short-form-links.tsv', newline='') as csvfile:
        spamreader = csv.DictReader(csvfile, delimiter='\t', quotechar='|')
        for row in spamreader:
            print(row)
            print(links_for_individual_short_forms)
            print('======')
            links_for_individual_short_forms[row['short_form_type']].append((row['link'],row['title']))


    for issue_title,issue_links in links_for_individual_short_forms.items():
        scrape_issue(issue_title, issue_links)

if __name__ == "__main__":
    main()