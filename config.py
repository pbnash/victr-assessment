class RepoListApp:
    """  A class to implement configuration options for the repo_list_app.py Flask application
         The application will instantiate and use the config method to retrieve configuration options """
    _config = {

        # Port number used by the Flask application
        "port"  : 5000,

        # Base URL for the github API repository searches
        "search_url" : "http://api.github.com/search/repositories",

	    # Parameters to customize the query.
        "search_parameters" : {
            "q" : [ 'is:public', 'language:python' ],
            "sort" : "stars",
            "order" : "desc",
            # Recommended per_page is 100 (max supported).  Must be between 1..100
            "per_page" :100,
        },
        #  Max count/rows for the local database table (repositories).
        #  Must be between 1..1000 (application-imposed max).
        "max_results" : 1000,

        # SQLite DB filename
        "db_name" : "repo_data.db",

        # App logging details
        "log_file"   : "repo_list.log",
        "log_level"  : "INFO",

        # Enable/disable status messages to stdout (e.g., during DB initialization)
        "show_messages" : True,

        # Enable/disable performing a full reload/refresh of the DB with current github search results
        "refresh_db"   : True,
    }


    @staticmethod
    def config(name):
        """  Returns the requested configuration item """
        return RepoListApp._config[name]
