from auth.models import User

# Simulazione database - sostituire con chiamata a MySQL
USERS = {
    "admin": {"id": 1, "username": "admin", "password": "admin123"}
}

def get_user_by_username(username):
    u = USERS.get(username)
    if u:
        return User(**u)
    return None

def get_user_by_id(user_id):
    for u in USERS.values():
        if u["id"] == int(user_id):
            return User(**u)
    return None

