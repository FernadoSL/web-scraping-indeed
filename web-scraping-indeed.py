from time import sleep
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import random
import math
import re
import sys
import json

def getIndeedUrl(country, job, location, indeedUri, limit):
    jobTerm = job.replace(' ','+')
    url = indeedUri.format(country, jobTerm, location, limit)
    return url

def startBrowser(url, webdriverPath):
    browser = webdriver.Chrome(webdriverPath)
    browser.get(url)
    return browser

def getNumberOfPages(limit, browser):
    resultsNumberString = browser.find_element_by_id('searchCountPages').text
    print('Results as string: ' + resultsNumberString)
    resultsNumber = int(re.findall('\d+', resultsNumberString.replace('.', ''))[1])
    print('Results: ' + str(resultsNumber))
    pages = math.ceil(resultsNumber/limit)
    print('Pages to visit: ' + str(pages) + '\n')
    
    return pages

def fetchData(data, browser, job_element):
    title, company, location, description = '', '', '', ''
    
    try:
        title =  browser.find_element_by_id('vjs-jobtitle').text
        company = browser.find_element_by_id('vjs-cn').text
        company = company.replace('- ', '')
        location = browser.find_element_by_id('vjs-loc').text
        description = browser.find_element_by_id('vjs-desc').text
    except NoSuchElementException:
        try:
            print('Unable to fetch data. Retrying.....')
            title = job_element.find_element_by_class_name('title').text
            location = job_element.find_element_by_class_name('location').text
            company = job_element.find_element_by_class_name('company').text
            company = company.replace('- ', '')
            description = job_element.find_element_by_class_name('summary').text
        except NoSuchElementException:
            print('Unable to fetch data.')

    print('Title: {} \nLocation: {} \nCompany: {} \nDescription: {} \n'.format(title, location, company, description))
    data = data.append({'job_title':title, 'company':company, 'location':location, 'job_description':description},ignore_index=True)
    return data

def scrape_indeed(url, browser, pages, limit, htmlRegex):
    data = pd.DataFrame(columns = ['job_title','company', 'location', 'job_description'])
    x = 0

    for j in range(pages):
        job_elements =  browser.find_elements_by_xpath(htmlRegex)
        try:
            for i in range(len(job_elements)):
                job_elements[i].click()
                data = fetchData(data, browser, job_elements[i])
        except:
            print("Fail to continue")
            
        url = url.replace('start=' + str(x),'start=' +str(x+limit))
        x += limit
        
        if len(job_elements) < limit:
            break
        
        browser.get(url)
        print('Moving on to page ' + str(j+2))
        sleep(2)

        try:
            browser.find_element_by_id('popover-x').click()
        except:
            print('No Newsletter Popup Found')
    
    browser.close()
    return data

def main():

    with open('config.json') as config_file:
        config = json.load(config_file)

    country = '.ca' # .com.br, .com, .ca
    location = 'Otawa' # 'Rio Grande do Sul'
    job = '.Net' # 'machine learning'
    limitPerPage = 50

    indeedUrl = getIndeedUrl(country, job, location, config['indeedUrl'], limitPerPage)
    browser = startBrowser(indeedUrl, config['webdriverPath'])
    pages = getNumberOfPages(limitPerPage, browser)

    data = scrape_indeed(indeedUrl, browser, pages, limitPerPage, config['htmlRegex'])
    data.to_csv(config['outputPath'])

if __name__ == "__main__":
    main()