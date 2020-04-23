Drug Navigator by Eunjae Shim

Final Project for SI-507 at UMich Winter 2020

Apr 22, 2020

The python scripts require the installation of the following python packages.
flask, sqlite3, plotly(.graph_objs in particular), bs4, requests

The program is made of three python scripts.

1. database_schema.py
The structure_links.csv (available https://www.drugbank.ca/releases/latest#structures) has information on >10000 drug compounds.
The State_Drug_Utilization_Data_2018.csv (available https://catalog.data.gov/dataset/state-drug-utilization-data-2018) has >1.5M records of drug utilization in the year of 2018 in different states.
Therefore the two files are not on github, but you can easily download them. Running the database_schema.py will produce the database that is necessary for running the app.

2. checkpoint.py
This script has the functions that are necessary for making requests and caching appropriate responses. 
It is imported in the actual flask app script.

3. htmlapp.py
The script that actually runs the flask html app.
Imports checkpoint.py to make appropriate requests to prepare data to be processed and presented.

By running htmlapp.py, you can access the drug navigator by entering 127.0.0.1:5000 in your web browser. You will initially see an index page where you can type in the name of a drug molecule that you want to search for and radio boxes for you to choose the information of interest. The use within the html pages are straightforward.
