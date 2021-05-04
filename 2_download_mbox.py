import os
from bs4 import BeautifulSoup
from tqdm import tqdm
import concurrent.futures
from urllib.request import urlopen

# Retrieve a single page and return the URL and content
def load_url(info, timeout):
    project_alias, folder_name, url = info.split(',')
    mbox_dir = "./mbox"
    path = mbox_dir + os.sep + project_alias + os.sep + folder_name + os.sep
    filename = url.split('/')[-1]
    # if the file exists then skip (i.e., resuming)
    if os.path.isfile(path + filename):
        print('file {} exists'.format(path + filename))
        return [None, None, None]
    try:
        with urlopen(url, timeout=timeout) as conn:
            con = conn.read()
    except Exception as e:
        print('cant read: {}, got an error: {}'.format(url, e))
        return [None, None, None]
    return [path, filename, con]

# Read url list with no '\n'
with open('./download_url_list.txt', 'r') as f:
    url_list = f.read().splitlines()

mbox_dir = "./mbox"
if not os.path.exists(mbox_dir):
    os.mkdir(mbox_dir)

cnt = 0
# We can use a with statement to ensure threads are cleaned up promptly
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    # Start the load operations and mark each future with its URL
    future_to_url = {executor.submit(load_url, url, 30): url for url in url_list}
    for future in concurrent.futures.as_completed(future_to_url):
        path, filename, content = future.result()
        url = future_to_url[future]
        cnt += 1
        # blank page
        if not content:
            continue
        # make dir
        if not os.path.exists(path):
            os.makedirs(path)
        # save mbox
        with open(path+filename, 'wb') as f:
            f.write(content)
            print('Processed: {}, Remaining: {} mbox'.format(url, len(url_list) - cnt))

print('All Done.')
with open('./log.log', 'w') as f:
    f.write('All Done!')