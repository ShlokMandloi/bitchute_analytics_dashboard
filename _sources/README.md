# Bitchute Analytics Dashboard from Web Scraped Data
This repository consists of 2 main components
Web Scraper Script - bitchute_scraper.py
Dash Plotly Dashboard - dash_app.py

bitchute_scraper.py is a standalone .ipynb script which can be run directly and scrapes data from https://api.bitchute.com/
The script scrapes posts from the following categories: News, Automobile, Entertainment, Business, Sports, Education and Health
If you wish to scrape any more or less categories, add/remove the category from the code. Make changes accordingly. (Categories are a bit hard-coded :P)
The script file will save seperate CSV files for each category in the project directory of the dash_app.py, after pre-processing, in the format " dash_csv_{category} "

Dash_app.py is a python script which creates a web-application dashboard on Dash Plotly (which is hosted on a server).
This script points to the project directory to read the 'cleaned' CSVs for each category.
CSVs are stored in dataframe variables and are manipulated simultaneously to create necessary plots for the dashboard.
There are 4 seperate subscripts callbacks.py , layout.py , custom.css and styles.css (in the assets folder)
It is necessary for these subscripts to be in the same directory to run, especially callbacks.py and layout.py. 'assets' deals with the aesthetics of the dashboard.

Dash App Dashboard hosted on AWS EC2 Instance. A Docker container was made to create a consistent environment. 
Connected to the EC2 instance using SSH, providing path to the locally downloaded EC2 Key Pair and the instance's public IP address
Installed Docker and Git on the EC2 instance, started the Docker service and added the EC2 user to the Docker.
Created a directory 'bitchute_app' in the EC2 instance. Cloned this GitHub repo in the made project directory.
Created a Dockerfile and installed the requirements.txt
Built the Docker Image using the Dockerfile
Ran the Docker Container in Detach Mode


The dashboard is running on this URL: http://54.234.243.223/

Jupyter Notebook deployed on GitHub Pages: https://shlokmandloi.github.io/bitchute_analytics_dashboard/scraper_bitchute.html

Steps to Run:
1. Clone the GitHub repo to the Desktop, for simplicity.
2. Run the scraper_bitchute.ipynb and make sure that the dash_csv_{category} CSV files, from the .ipynb script, are being saved in the repository project directory in the 'data' folder.
3. Open the app.py python script. This script creates the dashboard using Dash by Plotly.
4. Make sure that callbacks.py , layout.py and the .css scripts in the assets folder are in the same directory
5. Ensure that app.py care pointed to the CSV files (dash_csv_{category}.csv)
6. The requirements.txt in the GitHub repo is a library requirements file for app.py and not scraper_bitchute.ipynb (There are pip codelines in scraper_bitchute which installs all requirements needed for the script)
7. Once app.py runs correctly, it will say the following message 'Dash is running on http://0.0.0.0:80/', the dashboard may not open on the given link since it has been configured to be deployed to AWS EC2, to access the dashbord, click on the publicly available AWS IP address link above. The dashboard may not accessible locally. 




