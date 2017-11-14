# victr-assessment
VICTR Candidate Assessment assignment

Popular Python Repositories on GitHub
Using Python and a SQL database, complete the following:
1. Use the GitHub API to retrieve the most starred public Python projects.
Store the list of repositories in a database table. The table must contain the
repository ID, name, URL, created date, last push date, description, and
number of stars. This process should be able to be run repeatedly and
update the table each time.
Useful links from the GitHub API documentation:
https://developer.github.com/v3/
https://developer.github.com/v3/search/
2. Using the data in the table created in step 1, create a web application that
displays a list of the GitHub repositories and allows the user to click
through to view details on each one. Be sure to include all of the fields in
step 1 – displayed in either the list or detailed view.
3. Create a README file with a description of your architecture and notes on
installation of your application. You are free to use any Python, JavaScript,
or CSS frameworks as you see fit.

# Overview

This implementation uses SQLite3 for the SQL Database, and Flask to implement the web application.  The display of the 
GitHub repositories is managed via a rendered template, using JavaScript/jQuery and its DataTables plug-in.   
DataTables provides a nicely featured table interface that supports automatic pagination and filtering/search features, as 
well as self-contained styling options (no "standalone" CSS file is needed).

# Architecture/Implementation Details

The SQL database consists of a single table ('repositories').   Based on the JSON "items" structure returned by the 
GitHub search API (see:  https://developer.github.com/v3/search/#search-repositories ), the following fields are included:

repo_id (int, PRIMARY KEY)  -  JSON "id" value

description (text)          -  JSON "description" value

name (text)                 -  JSON "name" value

url (text)                  -  JSON "html_url" value

created (date)              -  JSON "created_at" value

pushed (date)               -  JSON "pushed_at" value

stars (int)                 -  JSON "stargazers_count" value

The Flask application (repo_list_app.py)  services two GET requests:  GET / (root), which renders the index.html template, 
and GET /repos, which is called via ajax from the template script.  GET /repos returns all of the repository information 
from the database that is then displayed in the DataTable.

## GitHub Search API interaction

The application uses unauthenticated access to the GitHub API.   The initial implementation imposes an application-specific
limit of 1000 records that will be maintained in the SQLite database.  This is also the maximum results Github will return
in a single search request (with a max of 100 per page).

This means that all of the data can be retrieved from GitHub in a single (paged) API request, so that rate limits enforced 
by GitHub (10 per minute for unauthenticated access) are not a factor.  (See To Do/Potential Enhancements)

##  Environment and installation

This was written for python3 (in a python3.6 virtual environment) and requires:

* pip install flask
* pip install requests

Other standard libraries used:  json, logging, os, requests, sqlite3, sys
Tested using Chrome on an Ubuntu Linux system.

## File Descriptions
config.py    -- contains options for the application, such as the name to use for the SQLite database file and other 
                runtime options,are managed here

repo_app_list.py   -  The main (Flask) application

templates/, 
templates/index.html   - the template file that will be rendered.  The templates directory is expected to be located in the 
                         same directory with the Flask application.

### Running the program
This is meant to be invoked directly (python3.6 repo_app_list.py).   It will utilize the port configured in config.py
(port 5000 by default; URL  http://localhost:5000   in the browser).   The application is not set up (yet) to daemonize.  
For demonstration purposes, it can just be run in the foreground.  The 'show_messages' option in the config.py file 
will enable some additional output to track progress on the database initialization.  Additional information is also logged
(per the configuration options).


### To Do items

* automated unit tests.  The code structure and flow needs improvement/refactoring to make it more easily testable
* Enhanced logic to allow multiple GitHub requests (up to 10).
* Performance profiling.  Confirm if the time it takes to do the initial database propulation is within reason.  Can it
  be improved by doing "batch"/executemany updates?
* Debug/resolve issues with having the DataTables plug-in make the ajax call to retrive the data.  Was getting an error.
As a workaround, made the ajax call from outside of the DataTables initialization function and passed in the data that
was retrieved
*  Full integration as a web app









