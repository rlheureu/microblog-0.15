from flask import jsonify, request, url_for, g
from app.models import Post, User
from app import db
from app.api import bp, auth
from app.api.auth import token_auth
from app.api.errors import bad_request
from datetime import datetime

@bp.route('/posts/<int:id>', methods=['GET'])
def get_post(id):
	return jsonify(Post.query.get_or_404(id).to_dict())

@bp.route('/posts', methods=['GET'])
def get_posts():
	page = request.args.get('page', 1, type=int)
	per_page = min(request.args.get('per_page', 10, type=int), 100)
	data = Post.to_collection_dict(Post.query, page, per_page, 'api.get_posts')
	return jsonify(data)

@bp.route('/user-<int:id>/posts', methods=['GET'])
def get_user_posts(id):
	# Check if user exists. If not, return a 404 error.
	user = User.query.filter_by(id=id).first()
	if user is None:
		return bad_request('No such user')
	
	# Create the parameters for pagination.
	page = request.args.get('page', 1, type=int)
	per_page = min(request.args.get('per_page', 10, type='int'), 100)
	
	# Find all the posts by that user. Prep and send the JSON payload.
	data = Post.to_collection_dict(Post.query.filter_by(user_id=user.id), page, per_page, 'api.get_user_posts', id=id)
	return jsonify(data)

@bp.route('/posts', methods=['POST'])
@token_auth.login_required 
def create_post():
	# Get JSON data from the client
	
	data = request.get_json() or {}

	# Ensure the data submitted is a complete request
	if 'body' not in data:
		return bad_request('Post body is empty! No post created.')
	
	# Ensure the user submitting is only submitting on behalf of themselves
	user = g.current_user
	data['user_id'] = user.id

	# Build the post and post it.
	post = Post()
	post.from_dict(data, new_post=True)
	db.session.add(post)
	db.session.commit()
	response = jsonify(post.to_dict())
	response.status_code = 201
	response.headers['Location'] = url_for('api.get_post', id=post.id)
	return response

@bp.route('/posts/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_post(id):
	# Ensure the post exists.
	post = Post.query.get_or_404(id)
	
	# Get the JSON data
	data = request.get_json() or {}

	# Update the timestamp
	data['timestamp'] = datetime.utcnow()

	# Update the post
	post.from_dict(data, new_post=False)
	db.session.commit()
	return jsonify(post.to_dict())