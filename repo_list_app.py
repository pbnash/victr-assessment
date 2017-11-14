import requests
import json
import sqlite3
import re
import logging

from flask import Flask, jsonify, request, render_template
from config import RepoListApp as My

app = Flask(__name__)
logging.basicConfig(filename=My.config('log_file'), level=My.config('log_level'))

REPO_DB_NAME = My.config('db_name')
db_conn = sqlite3.connect(REPO_DB_NAME)
db_cursor = db_conn.cursor()

# Definitions/query templates for managing the local SQLite DB
# This app refers to a hardcoded table name 'repositories' which it will instantiate in the DB

REPO_FIND           = "SELECT * FROM repositories WHERE repo_id=?"
REPO_INSERT         = "INSERT INTO repositories VALUES (?, ?, ?, ?, ?, ?, ?)"
REPO_DELETE         = "DELETE FROM repositories WHERE id=?"
REPO_GET_ALL_SORTED = "SELECT * FROM repositories ORDER BY stars DESC"
REPO_UPDATE         = '''UPDATE repositories
                        SET repo_id = ?, name = ?, description = ?, url = ?, created = ?, pushed = ?, stars = ?
                        WHERE repo_id = ?'''

DROP_REPO_TABLE     = "DROP TABLE IF EXISTS repositories"
CREATE_REPO_TABLE   = '''CREATE TABLE IF NOT EXISTS repositories
                       (repo_id int PRIMARY KEY, name text, description text, url text, created date, pushed date, stars int)'''

class Repository:
    """ A convenience class to create and update entries in the DB repository table  """

    def __init__(self, _id, name, desc, url, created, pushed, stars):
        self.repo_id = int(_id)
        self.name = name
        self.description = desc
        self.url = url
        self.created = created
        self.pushed = pushed
        self.stars = int(stars)

    def show(self):
        """ Produces formatted output describing the repository instance.  Useful during app development and testing  """
        for k, v in vars(self).items():
            print("{}: {}".format(k, v))
        print("\n")

    def save_to_db(self):
        """ Executes the appropriate SQL query (UPDATE or INSERT) to save the repository information in the DB. """
        params = list(vars(self).values())
        row = db_cursor.execute(REPO_FIND, (self.repo_id,)).fetchone()
        if row:
            # May be of interest if the repository information is already in the database.  Log as informational
            logging.info("Repository with id {} already exists.  Updating\n".format(self.repo_id))
            params.append(self.repo_id)  # VAR for the UPDATE WHERE clause
            db_cursor.execute(REPO_UPDATE, params)
        else:
            logging.debug("Inserting repo {} ({}) into DB\n".format(self.name, self.repo_id))
            db_cursor.execute(REPO_INSERT, params)

        db_conn.commit()


def make_search_query():
    """ Parses the search parameters defined in the config file and returns the resulting URL for the search query
        See: https://developer.github.com/v3/search/#search-repositories
    """

    query = My.config('search_url')
    if My.config('search_parameters'):
        query += '?'
        for key, val in My.config('search_parameters').items():
            query += key + '='
            if isinstance(val, list):
                for setting in val:
                    query += str(setting) + '+'
                query = re.sub('\+$', '&', query) # Replace trailing '+' with '&' (separator between parameters)
            else:
                query += str(val) + '&'

    return query[:-1]  # Strip the trailing '&' after the last parameter


def init_repo_db():
    """ Refreshes the SQLite database.  Interacts with github search API to retrieve the latest
        repository search results and repopulate the database with up-to-date repository descriptions
        Previous DB contents will be wiped.
        See: https://developer.github.com/v3/search/#search-repositories
    """

    if My.config('show_messages'):
        print("Building the database, please wait...", flush=True)

    db_cursor.execute(DROP_REPO_TABLE)
    db_cursor.execute(CREATE_REPO_TABLE)

    # Defaults used if expected config items are missing or outside of supported range
    per_page = My.config('search_parameters')['per_page']
    if not per_page or per_page <= 0 or per_page > 100:
        logging.warning('Invalid per_page option {} configured, using default of 100'.format(per_page))
        per_page = 100
    max_results = My.config('max_results')
    if not max_results or max_results <= 0 or max_results > 1000:
        logging.warning('Invalid max_results option {} configured, using default of 1000'.format(max_results))
        max_results = 1000

    this_page = make_search_query()
    logging.debug('Generated search query {}'.format(this_page))
    response = requests.get(this_page)

    if not response.ok:
        print(response)
        return

    # Will use the link information in the response header to traverse through the paged results (per Github implementation)
    if response.links:
        last_page = response.links["last"]["url"]
    else:
        last_page = this_page

    last_pass = max_results // per_page
    last_pass = (last_pass + 1) if max_results % per_page else last_pass
    passes = 1
    repo_count = 0

    while response.ok:
        search_results = json.loads(response.content)
        for item in search_results['items']:
            if repo_count == max_results:
                break
            # Extract values expected by the local DB table from the Github response body
            #
            col_values = [  int(item["id"]), item["name"], item["description"], item["html_url"],
                        item["created_at"], item["pushed_at"], int(item["stargazers_count"])
                     ]
            repo = Repository(*col_values)
            repo.save_to_db()
            repo_count += 1

        if My.config('show_messages'):
            progress = (passes/last_pass) * 100;
            print("{0:2d}%".format(int( (passes/last_pass) * 100)), flush=True)

        if this_page == last_page or repo_count == max_results or passes == last_pass:
            break

        passes += 1

        this_page = response.links["next"]["url"]
        response = requests.get(this_page)

    if My.config('show_messages'):
        print("Success!!", flush=True)


if __name__ == "__main__":
    if My.config('refresh_db'):
        init_repo_db()


    @app.route('/')
    def home():
        """ Homepage for the Flask application.  Renders the index.html template """
        return render_template('index.html')

    @app.route('/repos', methods=['GET'])
    def get_repos():
        """ GET /repos handler for the Flask Application.  Returns all the repository records (jsonified) in the SQLite DB """
        logging.debug(' Processing GET /repos request')
        rows = db_cursor.execute(REPO_GET_ALL_SORTED).fetchall()
        return (jsonify(rows))

    app.run(port=My.config('port'))
