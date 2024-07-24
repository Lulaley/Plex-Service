from flask import Blueprint, request, render_template, redirect, url_for
from .models import Post  # Importation d'un modèle hypothétique Post

posts = Blueprint('posts', __name__)

@posts.route('/posts')
def list_posts():
    all_posts = Post.query.all()  # Récupération de toutes les publications
    return render_template('posts/list.html', posts=all_posts)

@posts.route('/posts/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        # Logique pour créer une nouvelle publication
        new_post = Post(title=request.form['title'], content=request.form['content'])
        # Enregistrer new_post dans la base de données
        return redirect(url_for('posts.list_posts'))
    return render_template('posts/create.html')