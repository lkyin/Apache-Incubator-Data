import pandas as pd
import os
from tqdm import tqdm
import glob
import mailbox
import requests
from bs4 import BeautifulSoup

commit_path = './parsed_data/commits/'
commit_cols = ['proj_name','period','status', 'message_date', 'author_name', 'committer_name', 'file_path', 'addlines','dellines']
commit_files = glob.glob(os.path.join(commit_path, "*.csv"))

print('reading commits...')
df_from_each_file = (pd.read_csv(f, usecols = commit_cols) for f in commit_files)
commits_df = pd.concat(df_from_each_file, ignore_index=True)
print(commits_df.head())
# doesn't create a list, nor does it append to one
print('saving commits...')
commits_df.to_csv('./parsed_data/commits.csv', index=False)


email_path = './parsed_data/messages/'
email_cols = ['proj_name','mbox','folder','message_id', 'period', 'reference_id', 'status', 'message_date', 'sender_name']
e_files = glob.glob(os.path.join(email_path, "*.csv"))
print('reading emails...')
df_from_each_file = (pd.read_csv(f, usecols = email_cols) for f in e_files)
emails_df = pd.concat(df_from_each_file, ignore_index=True)
print(emails_df.head())
# doesn't create a list, nor does it append to one
print('saving emails...')
emails_df.to_csv('./parsed_data/emails.csv', index=False)
