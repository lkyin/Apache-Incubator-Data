# Apache-Incubator-Data
The repo (https://github.com/lkyin/Apache-Incubator-Data) contains the scripts for gathering mbox files (commits and emails) in Apache Incubator Projects. Further updates on the scripts and/or data may be available. 

## Dependencies

The scripts are validated under Linux Distribution `Ubuntu 16.04.6 LTS`, the code has been tested over `Python 2.7`.

Then install other dependencies (you may need to use pip2 only to correctly install those dependencies).

```
pip install -r requirements.txt
```

## Replication
To gather the data from ASF incubator projects, you can use code and data as follows. There may exist unepected cases if the ASF Incubator changes the way they store the data. The scripts and data are updated up to Feb, 2021. If further updates are available, please download/save the three .html files from: 

Project List: `https://incubator.apache.org/projects/`

Mailbox Files: `http://mail-archives.apache.org/mod_mbox/`

Attic Projects: `https://attic.apache.org/`

Put all three HTML files under the `source_html` folder.

- To obtain the mbox list:
  - Run `python 1_get_mbox_list.py`

- To concurrently download the mbox files (using `concurrent.futures` with `max_workers=10`): 
  - Run `python 2_download_mbox.py`

- There are some projects nested in the incubator folder (please refer to http://mail-archives.apache.org/mod_mbox/#incubator). To Extract those projects:
  - Run `python 3_arrange_nested_project.py`

- To remove the non-ASCII charactors: 
  - Run `python 4_remove_nonascii.py`

- To prase the mbox to individual csv files (it takes roughly 100 hrs on a single CPU): 
  - Run `python 5_parse_mbox.py` 

To join all the table into commits csv file and emails csv files:
  - Run `python 6_join_ASF_csvs.py` 

