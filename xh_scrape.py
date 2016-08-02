import requests
from bs4 import BeautifulSoup as bsp

import re
import os
import urllib.request as ureq
import sys

import socket
socket.setdefaulttimeout(120)

# g
_BASE_URL = 'http://xhamster.com'
BASE_URL = 'http://xhamster.com/photos'
URL_TYPE_DEAULT = 0
URL_TYPE_SHEMALE = 'shemale'
URL_TYPE_CUMSHOTS = 'cumshots'
URL_TYPE_INTERRACIAL = 'interracial'
URL_TYPE_FEMDOM = 'femdom'
URL_TYPE_LATIN = 'latin'
URL_TYPE_FACIALS = 'facials'


class Gallery(object):

    def __init__(self,title,num_images,link,views=0):
        self.title = title.replace('/','')
        self.num_images = num_images
        self.views = views
        self.link = link
        self.content = []

    def __str__(self):
        return '"{0}" has {1} images, seen by {2} people'.format(self.title,self.num_images,self.views)

    def fetch_content(self,log=False):
        # find slides url
        slides_url = get_soup(self.link).find('div',{'class' : 'gallery'}).find('a')['href']
        # scrape image src urls from slides page
        soup = get_soup(slides_url)
        # iterate through the slides 
        for i in range(self.num_images):
            # add src image to content
            img_tag = soup.find('img',{'class','slideImg'})
            if not img_tag:
                print('!!Something went wrong!!')
                break
            img_src = img_tag['src']
            if log:
                print('[{0}] {1}'.format(i,img_src))
            self.content.append(img_src)
            # get soup of next image slide
            soup = get_soup(soup.find('a',{'class','next'})['href'])

    def write(self,rel_path=None,log=False):
        # default relative path : title of gallery
        if rel_path is None:
            rel_path = self.title

        # check if folder exists
        if not os.path.exists(rel_path):
            os.makedirs(rel_path)

        # for each image in content list
        indices = list(range( 1,len(self.content)+1 ))
        for image_link,i in zip(self.content,indices):
            filename = '{0}/{1}_{2}'.format(rel_path,i,os.path.basename(image_link))
            if not os.path.isfile(filename):
                if log:
                    print('Downloading {}'.format(filename))
                try:
                    ureq.urlretrieve(image_link,filename)
                except socket.timeout:
                    print('Timeout while downloading [{}]\nSkipping it and moving on (Run the script again to fetch it)'.format(image_link))
            else:
                print('{} is already available'.format(filename))



def get_soup(url=BASE_URL):
    # raw content
    content = requests.get(url).content
    # soup
    return bsp(content,"lxml")

def get_galleries(url=BASE_URL):
    # get soup
    soup = get_soup(url)
    # find all gallery tags
    gallery_tags = soup.findAll('div',{'class' : 'gallery'})
    # list of galleries
    galleries = []
    for tag in gallery_tags:
        title = tag.find('u').string
        num_images = tag.find('span').text.replace(',','')
        views = tag.find('div',{'class' : 'views-value'}).string.replace(',','')
        link = tag.find('a')['href']
        galleries.append(Gallery(title=title,num_images=int(num_images),link=link,views = int(views)))
    # return a list of Gallery objects
    # sort : galleries.sort(key=lambda x: x.views,reverse=True)
    return galleries

def util_regex_params(tag_str):
    index = tag_str.rfind('[')
    endex = tag_str.rfind(' pictures')
    tlen = len(tag_str)
    title = tag_str[:index-1]
    return title, int(tag_str[index+1:endex])

def get_gallery_by_url(url,write=False):
    # get soup from url
    soup = get_soup(url)
    # find title and truncate it; number of images
    title, num_images = util_regex_params(soup.find('h1').text)
    # create gallery object
    gallery = Gallery(title=title,num_images=num_images,link=url)
    if write:
        # fetch content
        gallery.fetch_content(log=True)
        # write to disk
        gallery.write(log=True)
    return gallery
    

def gather_gallery_meta(niche=URL_TYPE_DEAULT,start=1,depth=10,k=0,log=False):
    # iterate through a 100 pages to get a list of galleries
    galleries = []
    for i in range(start,start+depth):
        url_i = decorate_url(niche,i)
        if log:
            print('Scraping {}'.format(url_i))
        galleries.extend(get_galleries(url=url_i))
    # we now have information about 100 pages of galleries
    #   lets sort them based on "views"
    galleries.sort(key=lambda x: x.views, reverse=True)
    if k:
        return galleries[:k]
    # return all
    return galleries

def decorate_url(niche,i):
    if niche == URL_TYPE_DEAULT:
        return '{0}/new/{1}.html'.format(BASE_URL,i)
    else:
        return '{0}/niches/new-{1}-{2}.html'.format(BASE_URL,niche,i)


if __name__ == '__main__':
    # user arguments
    if len(sys.argv) > 1:
        if _BASE_URL in sys.argv[1]:
            get_gallery_by_url(sys.argv[1],write=True)
    else:
        galleries = gather_gallery_meta(niche=URL_TYPE_FEMDOM,depth=10,k=0,log=True)
        for gallery in filter(lambda x : (x.num_images < 10), galleries):
            print('Fetching contents of {}'.format(gallery))
            gallery.fetch_content()
            gallery.write(log=True)
