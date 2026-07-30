from github import Github
from config import Config

class GitHubManager:
    def __init__(self):
        self.client = Github(Config.GITHUB_TOKEN)

    def create_repo(self, name):
        user = self.client.get_user()
        repo = user.create_repo(name)
        return repo

    def upload_file(self, repo, path, content):
        repo.create_file(path, "upload bot file", content)

    def update_file(self, repo, path, content):
        file = repo.get_contents(path)
        repo.update_file(path, "update bot file", content, file.sha)
