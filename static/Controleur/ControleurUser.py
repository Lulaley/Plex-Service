from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username, rights):
        self.id = username
        self.rights = rights

    @property
    def is_admin(self):
        return self.rights == "PlexService::Admin"

    @property
    def is_superadmin(self):
        return self.rights == "PlexService::SuperAdmin"

    @property
    def is_user(self):
        return self.rights == "PlexService::User"
