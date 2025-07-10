"""Interface to the problem database
"""


from flask import request
from presenter.rundb import get_latest_run_number
from presenter.rundb import get_rundb_info
from presenter.blueprints._auth import get_info
import requests
import datetime
from presenter.cache import cache



class lb_problemdb:
    """Class to interface with the problem database web API
    """
    def __init__(self, endpoint: str, target_app: str, audience: str,
                 access_token: str):
        """Initialize classe

        Args:
            endpoint (str): web address of the problem database
            target_app (str): target application (for identification)
            audience (str): audience (for identification)
            access_token (str): access token (for identification)
        """
        self.url = endpoint
        self.audience = audience
        self.access_token = access_token
        self.target_app = target_app
        self.token = 'initialtoken'
        self.expiration = datetime.datetime.now()

    def get_token(self) -> None:
        """Get access token from CERN SSO to login to the
        problem database
        """
        if datetime.datetime.now() < self.expiration:
            return
        r = requests.post(
            "https://auth.cern.ch/auth/realms/cern/api-access/token",
            auth=(self.audience, self.access_token),
            data={
                "grant_type": "client_credentials",
                "audience": self.target_app
            },
        )
        if r.ok:
            the_json = r.json()
            self.token = the_json["access_token"]
            expires_in_seconds = the_json["expires_in"]
            self.expiration = datetime.datetime.now() +\
                datetime.timedelta(seconds=expires_in_seconds)
        else:
            self.token = 'bad token'

    def auth_headers(self) -> dict[str, str]:
        """Get authorization HTML headers for the calls to the
        problem database

        Returns:
            dict[str, str]: dictionnary with authorization string
        """
        self.get_token()
        headers = {"Authorization": f"Bearer {self.token}"}
        return headers

    @cache.memoize(timeout=300)
    def search_issues(self, online: bool, run_number: int) -> list:
        """Search issues in the problem database

        Args:
            online (bool): True in online mode (will look for opened problems),
            False otherwise (will look for problems affecting the given run)
            run_number (int): run number for the issue

        Returns:
            list: list of problems for the run
        """
        if online:  # search opened problems
            the_args = {'open_or_closed_gte':
                        datetime.datetime.now().astimezone()}
        elif run_number:
            the_args = {'run_number': run_number}
        try:
            r = requests.get(f"{self.url}api/search/", the_args,
                             headers=self.auth_headers(), allow_redirects=False)
        except:
            return [{'system': 'Monitoring',
                     'title': 'Problem database not available',
                     'severity': 'Bad',
                     'id': 0}]
        problems = []
        if r.status_code == 200:
            print("Status:", r.status_code)
            print("Location:", r.headers.get("Location"))

            problems = r.json()
        return problems

    def create_issue(self, fields: dict[str, str]) -> bool:
        """Create an issue in the problem database

        Args:
            fields (dict[str, str]): dictionnary of informations needed for the
            problem database

        Returns:
            bool: True if success, False if failure
        """
        the_args = {'started_at': fields["started_at"],
                    'author_name': fields["author_name"],
                    'given_name': fields["given_name"],
                    'family_name': fields["family_name"],
                    'email': fields["email"],
                    'initial_comment': fields["initial_comment"],
                    'title': fields['title'],
                    'link': fields['link'],
                    'system_name': fields['system']}
        r = requests.post(f"{self.url}api/problems/", the_args,
                          headers=self.auth_headers())
        if r.status_code == 201:
            return True
        return False


class ProblemDBClient:
    """Class to interface between Monet and the problem DB
    """
    def __init__(self, endpoint: str, project_name: str, username: str,
                 key: str):
        """Initialize class

        Args:
            endpoint (str): endpoint (for authentication)
            project_name (str): project name (for authentication)
            username (str): user name (for authentication)
            key (str): passwork/token (for authentication)
        """
        self.endpoint = endpoint
        self.project_name = project_name
        self._client = lb_problemdb(endpoint, project_name, username, key)

    def get_fill_and_run(self, run_number: int) -> tuple[str, str]:
        """Get run information from the run database

        Args:
            run_number (int): run number

        Returns:
            tuple[str, str]: start and end time of the run
        """
        run_info = get_rundb_info(run_number)
        return run_info['starttime'], run_info['endtime']

    def submit_problem(self, username: str, system: str, title: str,
                       message: str, link: str,
                       run_number: int | bool) -> bool:
        """Submit a problem to the problem database

        Args:
            username (str): user name
            system (str): system name
            title (str): title of the problem
            message (str): description of the problem
            link (str): link to the logbook entry
            run_number (int | bool): run number (take the latest if False)

        Raises:
            RuntimeError: in case of access problem

        Returns:
            bool: True if success, False otherwise
        """
        if not run_number:
            run_number = get_latest_run_number(False,
                                               request.args.get('partition',
                                                                'LHCb'))
        starttime, endtime = self.get_fill_and_run(run_number)
        issue_fields = {
            "started_at": datetime.datetime.now().astimezone() if not endtime
            else starttime,
            "title": title,
            "author_name": get_info('cern_upn'),
            "given_name": get_info('given_name'),
            "family_name": get_info('family_name'),
            "email": get_info('email'),
            "initial_comment": message,
            "system": system.strip(),
            "link": link
        }
        if not self._client.create_issue(fields=issue_fields):
            raise RuntimeError("Problem database not accessible")
        return True

    def _get_problems(self, online: bool, run_id: int) -> list:
        """Get list of problems

        Args:
            online (bool): True in online mode, False otherwise
            run_id (int): run number

        Returns:
            list: list of problems
        """
        issues = self._client.search_issues(online, run_id)
        return issues

    def get_run_status(self, online: bool, run_id: int) -> dict:
        """Get list of issues for a rub

        Args:
            online (bool): True in online mode, False otherwise
            run_id (int): run number

        Returns:
            dict: dictionary of problems
        """
        problems = self._get_problems(online, run_id)
        result = {
            "status": "success" if problems == [] else "warning",
            "issues": []
        }
        for issue in problems:
            issue_status = 'warning'
            if issue["severity"] == "TRIVIAL":
                issue_status = 'success'
            elif issue["severity"] == "CRITICAL":
                issue_status = 'danger'
            elif issue["severity"] == "MINOR":
                issue_status = 'primary'
            elif issue["severity"] == "UNKNOWN":
                issue_status = 'light'

            result["issues"].append({
                "key": issue["id"],
                "summary": issue["system"] + ": " + issue["title"],
                "status": issue_status,
                "url": "https://lbproblems.cern.ch/problemdb/problems/"
                "{issue['id']}"
            })
        return result
