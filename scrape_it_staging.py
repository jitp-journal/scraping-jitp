# import necessary packages for webscraping.

from dataclasses import replace
from bs4 import BeautifulSoup
from urllib import request
from dateutil.parser import parse
import time
import random
import os
import re

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
        if raw_link.text.startswith('Issue') or raw_link['href'].startswith('https://jitp.commons.gc.cuny.edu/wp-content/plugins/peters-custom-anti-spam-image/custom_anti_spam.php'):
            pass
        elif raw_link.has_attr("title") and raw_link['title'] == "Share this article":
            pass
        elif raw_link['href'].endswith('#respond') or raw_link['href'].endswith('#comments') or '#comment' in raw_link['href']:
            pass
        elif raw_link.text in ['Attribution-NonCommercial-ShareAlike 4.0 International', 'Previous:', 'Next:', 'Learn how your comment data is processed', 'table of contents', 'Introduction /', 'JITP Issue 8 is now live! | Laura Wildemann Kane','JITP Issue 9 is now live! | Laura Wildemann Kane','Happenings – VREPS','Re-viewing Digital Technologies and Art History – DAHS','Wandering Volunteer Park /', '\n', 'Special Feature: Behind the Seams']:
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
        r'https:\/\/jitp\.commons\.gc\.cuny\.edu\/files\/[0-9]+\/[0-9]+|src="http:\/\/jitp\.commons\.gc\.cuny\.edu\/files\/[0-9]+\/[0-9]+',"images", img['src'])

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
        max_sleep = 5
        time.sleep(random.random() * max_sleep)
        print('=====')
        print('Scraping ' + issue_title)
        links_for_individual_issues[issue_title] = get_issue_link(issue_toc_link)
    
    return links_for_individual_issues

def main():
    # get all the main toc links
    # main_toc_links = get_main_toc_links()
    # no table of contents to speak of
    # main_toc_links.reverse()

    # use the main toc links to get each issue link
    # links_for_individual_issues = get_all_issue_links(main_toc_links)
    links_for_individual_issues = {'Issue Twenty One':[
        ('https://jitpstaging.commons.gc.cuny.edu/worth-the-time-exploring-the-faculty-experience-of-oer-initiatives/','Worth the time: Exploring the Faculty Experience of OER initiatives'),
        ('https://jitpstaging.commons.gc.cuny.edu/teaching-dh-on-a-shoestring-minimalist-digital-humanities-pedagogy/','Teaching DH on a Shoestring: Minimalist Digital Humanities Pedagogy'),
        ('https://jitpstaging.commons.gc.cuny.edu/dont-judge-a-book-but-what-about-the-professor-who-assigned-the-book/','Don’t Judge a Book—But What about the Professor Who Assigned the Book?'),
        ('https://jitpstaging.commons.gc.cuny.edu/an-interdisciplinary-case-study-of-cost-concerns-and-practicalities-for-open-educational-resources-at-a-hispanic-serving-institution-in-texas/','An Interdisciplinary Case Study of Cost Concerns and Practicalities for Open Educational Resources at a Hispanic- Serving Institution in Texas'),
        ('https://jitpstaging.commons.gc.cuny.edu/how-the-pandemic-transformed-us-the-process-and-practices-of-a-diversity-equity-inclusion-and-accessibility-focused-oer-project-for-teaching-and-learning-spanish/','How the Pandemic Transformed Us: The Process and Practices of a Diversity, Equity, Inclusion, and Accessibility-Focused OER Project for Teaching and Learning Spanish'),
        ('https://jitpstaging.commons.gc.cuny.edu/open-resources-for-corpus-based-learning-of-ancient-greek-in-persian/','Open Resources for Corpus-Based Learning of Ancient Greek in Persian'),
        ('https://jitpstaging.commons.gc.cuny.edu/five-faculty-and-library-curation-personas-to-aid-oer-discovery-solutions/','Five Faculty and Library Curation Personas to Aid OER Discovery Solutions'),
        ('https://jitpstaging.commons.gc.cuny.edu/implementing-oer-at-laguardia-community-college-three-case-studies/','Implementing OER at LaGuardia Community College: Three Case Studies'),
        ('https://jitpstaging.commons.gc.cuny.edu/creating-active-and-meaningful-learning-through-a-renewable-assignment-a-case-study-in-a-human-growth-development-psychology-course/','Creating Active and Meaningful Learning through a Renewable Assignment: A Case Study in a Human Growth Development Psychology Course'),
        ('https://jitpstaging.commons.gc.cuny.edu/building-a-community-of-voices-in-professional-writing/','Building a Community of Voices in Professional Writing')   
    ]
    }
    for issue_title,issue_links in links_for_individual_issues.items():
        scrape_issue(issue_title, issue_links)

if __name__ == "__main__":
    main()