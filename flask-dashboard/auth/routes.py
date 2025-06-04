from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user
from auth.models import User
from utility.auth_utils import get_user_by_username

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_by_username(username)

        if user and user.password == password:
            login_user(user)
            flash('Login effettuato con successo.', 'success')
            return redirect(url_for('overview.index'))

        # Messaggio di errore se le credenziali sono errate
        flash('Credenziali errate. Riprova.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('authentication/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout effettuato con successo.', 'success')
    return redirect(url_for('auth.login'))
