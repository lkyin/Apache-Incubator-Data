#coding: utf-8
import os
import mailbox
import bs4
import email
import re
import pandas as pd
import json
from tqdm import tqdm
from email.header import decode_header
from datetime import datetime
from dateutil import parser
import math
pd.set_option('display.max_columns', None)


def compute_date(end_date, current_date):
    # returns a timedelta object 
    end_date_obj = datetime.strptime(end_date, '%m/%d/%Y')
    # datetime.datetime(1999, 8, 28, 0, 0) -> parser.parse("Aug 28 1999 12:00AM")
    current_date_obj = parser.parse(current_date).replace(tzinfo=None)
    # current_date_obj = datetime.strptime(current_date, '%Y-%m-%dT%H:%M:%SZ')
    period = (current_date_obj - end_date_obj).days / 30
    return int(period)


def get_info(message):
    #return: cname,caddress,aname,aaddress,msg_format
    str_message = message.as_string()
    #if it is from svn, author = committer
    if message['X-Mailer'] and 'Git' not in message['X-Mailer']:
        msg_format = 'SVN'
        name, address = email.utils.parseaddr(message["from"])
        # if no name
        if not name:
            if "\nAuthor:" in str_message:
                namepos1 = str_message.index("\nAuthor:")
                name = str_message[namepos1:namepos1+100].split("\n")[1].split(" ")[1]
                # name = asciiCodify(name)
            else:
                name = address.split('@')[0]
        return name, address, name, address, msg_format

    #if it is git msg: contains 'X-Mailer: ASF-Git Admin Mailer' or 'X-Git'
    elif 'X-Git-' in message:
        msg_format = 'Git'
        try:
            author_string = "\nAuthor:"
            namepos1=str_message.index(author_string)
            string_left = len(author_string) + 1
            ccount= string_left
            while(str_message[namepos1+ccount]!='\n'):
                ccount=ccount+1                
            aname=str_message[string_left:namepos1+ccount].split(' <')[0]
            aaddress=str_message[string_left:namepos1+ccount].split(' <')[1].split('>')[0]
        except:
            cname, caddress = email.utils.parseaddr(message["from"])
            cname = caddress.split('@')[0]
            return cname, caddress, None, None, msg_format
        try:
            committer_string = "\nCommitter:"
            namepos2 = str_message.index(committer_string)
            string_left = len(committer_string) + 1
            ccount= string_left
            while(str_message[namepos2+ccount]!='\n'):
                ccount=ccount+1                
            cname = str_message[string_left:namepos2+ccount].split(' <')[0]
            caddress = str_message[string_left:namepos2+ccount].split(' <')[1].split('>')[0]
        except:
            cname, caddress = email.utils.parseaddr(message["from"])
            cname = caddress.split('@')[0]
        return cname, caddress, aname, aaddress, msg_format

    #is email
    elif "from" in message:
        msg_format = 'EMAIL'
        name, address = email.utils.parseaddr(message["from"])
        # name = asciiCodify(name)
        if not name:
            name = address.split('@')[0]
        return name, address, name, address, msg_format
    else:
        return None, None, None, None, None


def get_datetime(message):
    if len(message["date"].split(" "))>4:
        datetime = message["date"]
    if '(' in datetime:
        delLen=-len(datetime.split("(")[1])-2
        datetime=datetime[:delLen]
    tempdate=str(re.search(r'([0-9]+) ([\w]+) ([0-9]+) ([0-9]+):([0-9]+):([0-9]+) ([\W]+[0-9]+)', str(datetime)).group())
    tempdate=tempdate.split(' ')
    if len(tempdate[0])<4 and len(tempdate[2])<4:
        tempdate[2]="20"+tempdate[2]
        datetime=' '.join(tempdate)
    return datetime

#is svn, commit datetime = message datetime                   
def process_svn_commit(message, body):
    
    num = -1
    mlen=len(body)
    commits = []
    adate = None
    cdate = None
    sha = None

    while num < mlen-1:
        addlines = 0
        dellines = 0
        fileop= ''
        filename= ''
        num+=1

        # check if it's a new line
        if body[num-1] !='\n':
            continue
        # remove files
        if body[num:num+8]=='Removed:':
            fileop="remove"
            num=num+9
            addlines = 0
            dellines = 0

            while (body[num]==' '):
                ccount=0
                while(body[num+ccount]!='\n'):
                    ccount=ccount+1
                filename=body[num+4:num+ccount]
                num=num+ccount+1
                commits.append([adate, cdate, sha, filename, fileop, addlines, dellines])


        # Copied folders
        if body[num:num+7]=='Added:\n':
            fileop = "copy"
            num = num+7
            addlines = 0
            dellines = 0
            while (body[num]==' '):
                ccount=0
                while(body[num+ccount]!='\n'):
                    ccount=ccount+1
                filename=body[num+4:num+ccount]
                num=num+ccount+1
                filepath=[]
                if body[num+4:num+19]=="  - copied from" and filename[-1]=='/':
                    ccount=0
                    while(body[num+ccount]!='\n'):
                        ccount=ccount+1
                    oldfilename=body[num:num+ccount].split(", ")[-1]
                    num=num+ccount+1  
                commits.append([adate, cdate, sha, filename, fileop, addlines, dellines])             
        
        # Add new file
        if body[num:num+7]=='Added: ':
            fileop="add"
            num=num+7
            ccount=0
            addlines=0
            dellines=0
            while(body[num+ccount]!='\n'):
                ccount=ccount+1
            filename=body[num:num+ccount]#get the name of added file
            flag_startcount=0
            while num<mlen-2:
                num+=1
                if body[num-1]!='\n':
                    continue
                if body[num]=="=" and flag_startcount==0:
                    flag_startcount=1
                    continue
                if body[num]=='\n' and body[num+1].isalpha() and flag_startcount:#end of the file
                    break
                if body[num]=='+' and body[num+1]!='+':
                    addlines+=1
            commits.append([adate, cdate, sha, filename, fileop, addlines, dellines])
    
        # Modified
        if body[num:num+10]=='Modified: ':
            fileop="mod"
            num=num+10
            ccount=0
            addlines=0
            dellines=0
            while(body[num+ccount]!='\n' and body[num+ccount]!='\r'):
                ccount=ccount+1
            filename=body[num:num+ccount]#get the name of modified file  
            flag_startcount=0
            while num<mlen-2:
                num+=1
                if body[num-1]!='\n':
                    continue
                if body[num]=="=" and flag_startcount==0:
                    flag_startcount=1
                elif body[num]=='\n' and body[num+1].isalpha() and flag_startcount:#end of the file
                    break
                elif body[num]=='+' and body[num+1]!='+':
                    addlines+=1
                elif body[num]=='-' and body[num+1]!='-':
                    dellines+=1
            commits.append([adate, cdate, sha, filename, fileop, addlines, dellines])

        # Copy                 
        if body[num:num+8]=='Copied: ':
            fileop="copy"
            num=num+8
            ccount=0
            addlines=0
            dellines=0
            while(body[num+ccount]!='\n'):
                ccount=ccount+1
            name_in=body[num:num+ccount]#get the name of copied file
            filename=name_in.split(" ")[0]
            oldfilename=name_in.split(", ")[-1].split(")")[0]

            flag_startcount=0
            while num<mlen-2:
                num+=1
                if body[num-1]!='\n':
                    continue
                if body[num]=="=" and flag_startcount==0:
                    flag_startcount=1
                elif body[num]=='\n' and body[num+1].isalpha() and flag_startcount:#end of the file
                    break
                elif body[num]=='+' and body[num+1]!='+':
                    addlines+=1
                elif body[num]=='-' and body[num+1]!='-':
                    dellines+=1

                commits.append([adate, cdate, sha, filename, fileop, addlines, dellines])

    return commits


def process_git_commit(message, body):
    # initialization
    fileop= ''
    filename= ''
    num = -1
    mlen=len(body)
    commits = []
    str_message = message.as_string()

    # use regular exp to get the commit date and author date
    # author date
    r1 = re.search(r"\nAuthored: (.*?)\n", str_message)
    r2 = re.search(r"\nAuthorDate: (.*?)\n", str_message)
    adate = r1.group(1) if r1 else ''
    adate = r2.group(1) if r2 else ''

    # commit date
    r3 = re.search(r"\nCommitted: (.*?)\n", str_message)    
    cdate = r3.group(1) if r3 else ''

    # sha
    r4 = re.search(r"\nCommit: (.*?)\n", str_message)
    r5 = re.search(r"\nX-Git-Rev: (.*?)\n", str_message)
    sha = r4.group(1) if r4 else ''
    sha = r5.group(1) if r5 else ''

        
    '''
    adate = str_message.split("\nAuthored: ")[1].split("\n")[0] or \
        str_message.split("\nAuthorDate: ")[1].split("\n")[0]
    
    cdate = str_message.split("\nCommitted: ")[1].split("\n")[0]
    
    sha = str_message.split("\nCommit: ")[2].split("\n")[0] or \
        str_message.split("\nX-Git-Rev: ")[1].split("\n")[0]
    #sha=None
    '''

    while (num < mlen):
        num+=1
        if body[num-1] != '\n':
            continue
        
        # loop until getting the single file path
        if body[num:num+6]=='http:/':
            ccount=7
            while(body[num+ccount]!='\n'):
                ccount=ccount+1
            filename = body[num+7:num+ccount]

        # loop until getting previous filename and current file name
        if body[num:num+6]=='diff -' and filename:
            oldname=''
            # read file names before commit and after commit
            while num<mlen:
                # check if is a newline
                if body[num]!='\n':
                    num+=1
                    continue

                if body[num+1:num+5]=='--- ':
                    ccount=1
                    while(body[num+ccount]!='\n'):
                        ccount=ccount+1
                    oldname=body[num+6:num+ccount]
                    num=num+ccount
                    ccount=1
                    while(body[num+ccount]!='\n'):
                        ccount=ccount+1
                    newname=body[num+6:num+ccount]
                    num=num+ccount
                    break
                num+=1
        
            if oldname=='':
                print('No oldname, something is wrong')
                break
            elif oldname==newname:#give a file operation based on filename changes
                fileop='mod'
           
            elif oldname=='dev/null\r' or oldname=='dev/null':
                fileop='add'

            elif newname=='dev/null\r' or newname=='dev/null':
                fileop='del'
            else:
                fileop='copy'
                
            addlines = 0
            dellines = 0
            while (num<mlen-6 and body[num:num+6]!='\nhttp:'):
                num=num+1
                if body[num:num+2]=='\n+' and body[num+2]!='+':
                    addlines+=1
                elif body[num:num+2]=='\n-' and body[num+2]!='-':
                    dellines+=1
            commits.append([adate, cdate, sha, filename, fileop, addlines, dellines])
    return commits

# getting plain text 'email body'
def get_body(message):
    body = None
    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
                for subpart in part.walk():
                    if subpart.get_content_type() == 'text/plain':
                        body = subpart.get_payload(decode=True)
            elif part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True)
    elif message.get_content_type() == 'text/plain':
        body = message.get_payload(decode=True)
    return body


def email_source(subject):
    msg_format = None
    if len(subject) < 4:
        return msg_format
    elif subject[0:3]=='Re:':
        msg_format='EMAIL'
    elif subject[0:4]=='svn ':
        msg_format='SVN'
    return msg_format

def get_subject(subject):
    subject_parts = []
    subjects = decode_header(subject)
    for content, encoding in subjects:
        try: 
            subject_parts.append(content.decode(encoding or "utf8"))
        except:
            subject_parts.append(content)

    return "".join(subject_parts)

def divide_chunks(l, n): 
    # looping till length l 
    for i in range(0, len(l), n):  
        yield l[i:i + n] 

with open('./end_date_dict.json', 'r') as f:
    end_dict = json.load(f)


df = pd.read_csv("./project_info.csv")
project_info_dict = dict([(alias, [pid, name, alias, status, s_date, e_date]) for pid, name, alias, status, s_date, e_date in \
    zip(df.listid, df.listname,df.pj_alias,df.status,df.start_date,df.end_date)])


base_path = './ascii_mbox'
project_list = os.listdir(base_path)

target_folder = './parsed_data/commits'
if not os.path.exists(target_folder):
    os.makedirs(target_folder)

target_folder = './parsed_data/messages'
if not os.path.exists(target_folder):
    os.makedirs(target_folder)


messages_columns = ['proj_name', 'mbox', 'folder', 'message_id', 'period', 'status', 'reference_id', 'message_date', \
                       'sender_email', 'sender_name', 'receiver_email', 'cc_list', \
                       'subject', 'content', 'source']

commits_columns = ['proj_name', 'mbox', 'folder', 'message_id', 'period', 'status', 'message_date', \
                    'author_date', 'commit_date', 'author_name', 'author_email', \
                    'committer_name', 'committer_email', 'msg_format',\
                    'file_path', 'file_op', 'addlines', 'dellines', 'source']

num_error = 0
for proj in tqdm(project_list):
    if proj == 'asf-wide' or proj == 'incubator' or proj == 'attic':
        continue

    mbox_id_set = set()
    project_path = base_path+os.sep+proj
    p_folders = os.listdir(project_path)
    p_name = proj.replace('.incubator', '')
    # set the project basic info
    pid, name, alias, status, s_date, e_date = project_info_dict[p_name] if p_name in project_info_dict \
                                                                else [None, None, None, 'incubating', None, None]
    for folder in p_folders:
        folder_path = project_path+os.sep+folder
        mboxes = os.listdir(folder_path)
        messages_df = pd.DataFrame(columns=messages_columns)
        commits_df = pd.DataFrame(columns=commits_columns)
        for mbox in mboxes:
            mbox_path = folder_path+os.sep+mbox
            print(mbox_path)
            mbox_obj = mailbox.mbox(mbox_path)
            # process each mbox
            for idx, message in enumerate(mbox_obj):
                try:
                    message_id = message["message-id"]
                    if (not message_id) or (message_id in mbox_id_set):
                        continue
                    mbox_id_set.add(message_id)
                    email_body = get_body(message)
                    if not email_body:
                        continue
                    try:
                        email_body = email_body.decode("utf-8")
                    # cant encode as UTF-8 try latin-1 coding
                    except UnicodeDecodeError as e:
                        email_body = email_body.decode('latin-1')
                    cleaned_body = email_body.replace('\n', ';').replace('\t', ';')

                    # message obj does care the lower/upper case
                    email_cc = message['cc']
                    email_subject = str(message["Subject"])
                    email_date = get_datetime(message)
                    email_to = message['To']
                    email_reference_id = message["in-reply-to"]
                    
                    committer_name, committer_address, author_name, author_address, msg_format = get_info(message)
                    # update the format
                    msg_format = email_source(email_subject) or msg_format
                    to_write = {}
                    if msg_format == 'Git':
                        commits = process_git_commit(message, email_body)
                        for commit in commits:
                            to_write = {}
                            adate, cdate, sha, filename, fileop, addlines, dellines = commit
                            # things to write
                            to_write['proj_name'] = p_name
                            to_write['folder'] = folder
                            to_write['message_id'] = message_id
                            to_write['message_date'] = email_date
                            to_write['period'] = compute_date(e_date, email_date) if e_date else None
                            to_write['author_date'] = adate
                            to_write['commit_date'] = cdate
                            # to_write['SHA'] = sha
                            to_write['mbox'] = mbox
                            to_write['source'] = 'ASF'
                            to_write['status'] = status
                            to_write['committer_name'] = committer_name
                            to_write['committer_email'] = committer_address
                            to_write['author_name'] = author_name
                            to_write['author_email'] = author_address
                            to_write['msg_format'] = msg_format
                            to_write['file_path'] = file_path
                            to_write['file_op'] = fileop
                            to_write['addlines'] = addlines
                            to_write['dellines'] = dellines
                            # to_write['subject'] = email_subject
                            # to_write['content'] = cleaned_body
                            commits_df = commits_df.append(to_write, ignore_index = True)


                    if msg_format == 'SVN':
                        commits = process_svn_commit(message, email_body)
                        for commit in commits:
                            to_write = {}
                            adate, cdate, sha, filename, fileop, addlines, dellines = commit
                            # things to write
                            to_write['proj_name'] = proj.replace('.incubator', '')
                            to_write['folder'] = folder
                            to_write['message_id'] = message_id
                            to_write['message_date'] = email_date
                            to_write['period'] = compute_date(e_date, email_date) if e_date else None
                            to_write['author_date'] = adate
                            to_write['commit_date'] = cdate
                            # to_write['SHA'] = sha
                            to_write['mbox'] = mbox
                            to_write['status'] = status
                            to_write['source'] = 'ASF'
                            to_write['committer_name'] = committer_name
                            to_write['committer_email'] = committer_address
                            to_write['author_name'] = author_name
                            to_write['author_email'] = author_address
                            to_write['msg_format'] = msg_format
                            to_write['file_path'] = filename
                            to_write['file_op'] = fileop
                            to_write['addlines'] = addlines
                            to_write['dellines'] = dellines
                            # to_write['subject'] = email_subject
                            # to_write['content'] = cleaned_body
                            commits_df = commits_df.append(to_write, ignore_index = True)


                    if msg_format == 'EMAIL':
                        to_write = {}
                        to_write['proj_name'] = proj.replace('.incubator', '')
                        to_write['mbox'] = mbox
                        to_write['folder'] = folder
                        to_write['message_id'] = message_id
                        to_write['reference_id'] = email_reference_id
                        to_write['message_date'] = email_date
                        to_write['source'] = 'ASF'
                        to_write['status'] = status
                        to_write['period'] = compute_date(e_date, email_date) if e_date else None
                        to_write['sender_name'] = author_name
                        to_write['sender_email'] = author_address
                        to_write['receiver_email'] = email_to
                        to_write['cc_list'] = email_cc
                        to_write['subject'] = email_subject
                        # to_write['content'] = cleaned_body
                        messages_df = messages_df.append(to_write, ignore_index = True)
                except Exception as e:
                    print(e)
                    num_error += 1
                    continue

        # stores as per project per category
        if not messages_df.empty:
            messages_df.to_csv('./parsed_data/messages/{}-{}-messages.csv'.format(proj, folder))
        if not commits_df.empty:
            commits_df.to_csv('./parsed_data/commits/{}-{}-commits.csv'.format(proj, folder))


with open('log.log', 'w') as f:
    f.write('Done. Ignored {} Messages'.format(num_error))




