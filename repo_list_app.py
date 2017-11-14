
import json
import logging
import os
import requests
import sqlite3


from flask import Flask, jsonify, request, render_template
from config import RepoListApp as My

app = Flask(__name__)
logging.basicConfig(filename=My.config('log_file'), level=My.config('log_level'))

db_conn = sqlite3.connect(My.config('db_name'))
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


    def get_from_db(self):
        row = db_cursor.execute(REPO_FIND, (self.repo_id,)).fetchone()
        return row

    def save_to_db(self):
        """ Executes the appropriate SQL query (UPDATE or INSERT) to save the repository information in the DB. """

        params = list(vars(self).values())
        if self.get_from_db():
            # May be of interest if the repository information is already in the database, since the DB is
            # generally built from scratch each time application is run.  Log as informational
            logging.info("Repository with id {} already exists.  Updating\n".format(self.repo_id))
            params.append(self.repo_id)  # VALUE for the WHERE clause
            db_cursor.execute(REPO_UPDATE, params)
        else:
            logging.debug("Inserting repo {} ({}) into DB\n".format(self.name, self.repo_id))
            db_cursor.execute(REPO_INSERT, params)

        db_conn.commit()



def init_repo_db():
    """ Refreshes the SQLite database.  Interacts with github search API to retrieve the latest
        repository search results and repopulate the database with up-to-date repository descriptions
        Previous DB contents will be wiped.
        See: https://developer.github.com/v3/search/#search-repositories
    """

    err_status = None
    if My.config('show_messages'):
        print("Building the database, please wait...", flush=True)

    try:
        db_cursor.execute(DROP_REPO_TABLE)
        db_cursor.execute(CREATE_REPO_TABLE)

        # Sanity check config items
        per_page = My.config('search_parameters')['per_page']
        if not per_page or per_page <= 0 or per_page > 100:
            raise ValueError('Invalid per_page value in configuration')
        max_results = My.config('max_results')
        if not max_results or max_results <= 0 or max_results > 1000:
            raise ValueError('Invalid max_results value in configuration')

        r = requests.get(My.config('search_url'), params=My.config('search_parameters'))
        r.raise_for_status()
        # Will use the link information in the response header to traverse through the paged results (per Github implementation)
        if r.links:
            last_page = r.links["last"]["url"]
        else:
            last_page = r.url

        # For generating progress indication
        last_pass = (max_results // per_page)
        if (max_results % per_page):
            last_pass += 1
        passes = 1
        repo_count = 0

        while r.ok:
            search_results = json.loads(r.content)
            for item in search_results['items']:

                # Extract values expected by the local DB table from the Github response body
                col_values = [  int(item["id"]), item["name"], item["description"], item["html_url"],
                                item["created_at"], item["pushed_at"], int(item["stargazers_count"])
                             ]
                repo = Repository(*col_values)
                repo.save_to_db()
                repo_count += 1
                if repo_count == max_results:
                    break

            # Progress indicator...
            if My.config('show_messages'):
                print("{0:2d}%".format(int( (passes/last_pass) * 100)), flush=True)

            if r.url == last_page or repo_count == max_results:
                break

            passes += 1
            r = requests.get(r.links["next"]["url"])
            r.raise_for_status()

        if My.config('show_messages'):
            print("Success!!", flush=True)

    except ValueError as err:
        logging.error('Value error: {}'.format(err))
        err_status = err
    except requests.exceptions.RequestException as err:
        logging.error('An error occurred while executing a GitHub API request: {}'.format(err))
        err_status = err
    except sqlite3.Error as err:
        logging.error('A database error occurred: {}'.format(err))
        err_status = err
    except:https://github.com/pbnash/victr-assessment.git
        err_status = err
    finally:
        if err_status:
            raise err_status
        return


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
        try:
            rows = db_cursor.execute(REPO_GET_ALL_SORTED).fetchall()
            if not rows:
                return {"message":  "No repositories found"}, 404
            else:
                return (jsonify(rows))

        except Exception as err:
            logging.error(err)
            return {"messsage": "A database error occurred"}, 500

    app.run(port=My.config('port'))
