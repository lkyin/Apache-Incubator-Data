from urllib.request import urlopen
import codecs
import unicodedata
import sys
import os
import time
import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm

# last modified
html_date = '2021.2'
STATUS = ['incubating', 'graduated', 'retired']

Name2id_set = {
    'zetacomponents': 'zeta',
    'hadoopdevelopmenttools(hdt)': 'hdt',
    'climatemodeldiagnosticanalyzer': 'cmda',
    'openofficeorg': 'openoffice',
    'openoffice.org': 'openoffice',
    'openclimateworkbench': 'climate',
    'empire-db': 'empire',
    'beanvalidation': 'bval',
    'amber': 'oltu',
    'lucene.net': 'lucenenet',
    'xmlbeanscxx': 'xmlbeans-cxx',
    'odftoolkit': 'odf'
}

# baseurl = 'http://mail-archives.apache.org/mod_mbox/'
# KEYWORD_commit = ['-commits', '-svn', '-cvs', '-scm']
# KEYWORD_dev = ['-dev', '-issues', '-notifications']

def read2soup(url):
    con = urlopen(url)
    doc = con.read()
    con.close()
    soup = BeautifulSoup(doc, "html.parser")
    return soup

def check_pj_id(name_in):
    if name_in in Name2id_set:
        return Name2id_set[name_in]
    return name_in

# Fix any characters that might mess up script
def escape(s):
    return unicode(s.replace("'", "''").replace('%', '%%'))

# Graduated project but now in attic
soup_attic = BeautifulSoup(
    open(
        'source_html/Apache Attic(' + html_date + ').html'),
    "html.parser")
temp_contentin = soup_attic.html.body.findAll('div')[19]
temp_list = temp_contentin.findAll('li')
attic_list = []
for i in range(len(temp_list)):
    attic_list.append(str(temp_list[i]).split('.html')[0].split('/')[-1])

# All projects
soup1 = BeautifulSoup(
    open(
        'source_html/Apache Projects List(' +
        html_date +
        ').html'),
    "html.parser")

temp_listin = soup1.html.body.findAll('tr')
PJ_list_info = []
PJ_alias_list = []
PJstatus = -1
for i in range(len(temp_listin)):
    if str(temp_listin[i].find('th')) == '<th>Project</th>':
        PJstatus += 1
        continue
    PJname = temp_listin[i].find('a').text
    PJid = check_pj_id(str(temp_listin[i]).split('"')[1])
    PJsponsor = temp_listin[i].findAll('td')[2].text
    PJintro = temp_listin[i].findAll('td')[1].text
    PJstartdate = datetime.datetime.strptime(
        temp_listin[i].findAll('td')[4].text, "%Y-%m-%d").date()
    PJenddate = 'NULL'
    PJ_url = 'http://incubator.apache.org' + \
        (str(temp_listin[i].find('a')['href']))
    if PJstatus > 0:
        PJenddate = datetime.datetime.strptime(
            temp_listin[i].findAll('td')[5].text, "%Y-%m-%d").date()

    in_attic = True if PJid in attic_list else False
    # if check_pj_id()
    PJ_list_info.append([PJid,
                         PJname,
                         PJstatus,
                         PJsponsor,
                         PJstartdate,
                         PJenddate,
                         0,
                         0,
                         in_attic,
                         PJintro,
                         PJ_url])
    # 0 for this project is not available,one for has dev,one for has commit
    PJ_alias_list.append(PJid)

soup2 = BeautifulSoup(
    open(
        'source_html/Available Mailing Lists(' +
        html_date +
        ').html'),
    "html.parser")

PJ_name = soup2.html.body.findAll('h3')
PJ_listin = soup2.html.body.findAll('li')

k = 0
PJlist = []
# get available list name from mailbox
for i in range(0, len(PJ_name)):  
    temp = PJ_listin[k].findAll('a')
    PJlist.append(temp)
    k = k + len(temp)

url_list = []
for project in tqdm(PJlist):
    for folder in project:
        url = folder.get('href')
        folder_name = folder.text
        if not url:
            project_alias = folder.get('name')
            continue
        soupin = read2soup(url)
        listin = soupin.html.body.findAll('span')
        for item in listin:
            datetime = item['id'] 
            this_url = url + datetime + ".mbox"
            url_list.append([project_alias, folder_name, this_url])

print(len(url_list))
with open("download_url_list.txt", "w") as f:
    for project_alias, folder_name, this_url in url_list:
        f.write('{},{},{}'.format(project_alias, folder_name, this_url) + '\n')