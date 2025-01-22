from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import psycopg2
import os

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Environment variable for admin password
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '****')  # Default value is a placeholder

# Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),           # Get DB host from env
            database=os.getenv('DB_NAME', 'ps_project'),     # Get DB name from env
            user=os.getenv('DB_USER', 'postgres'),           # Get DB user from env
            password=os.getenv('DB_PASSWORD')                # Get DB password from env
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to database: {e}")
        return None
    



# Poll creation route
@app.route('/create_poll', methods=['POST'])
def create_poll():
    data = request.get_json()
    question = data['question']
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection failed!"}), 500

    cur = conn.cursor()
    cur.execute('INSERT INTO polls (question) VALUES (%s) RETURNING id', (question,))
    poll_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"poll_id": poll_id, "message": "Poll created successfully!"})

# Option addition route
@app.route('/add_option', methods=['POST'])
def add_option():
    data = request.get_json()
    poll_id = data['poll_id']
    option_text = data['option_text']
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection failed!"}), 500

    cur = conn.cursor()
    cur.execute('INSERT INTO options (poll_id, option_text) VALUES (%s, %s)', (poll_id, option_text))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Option added successfully!"})

# Voting route
@app.route('/vote', methods=['POST'])
def vote():
    data = request.get_json()
    user_token = data['token']
    option_id = data['option_id']

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection failed!"}), 500

    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE token = %s', (user_token,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return jsonify({"message": "Invalid token!"}), 401

    cur.execute('SELECT * FROM votes WHERE user_token = %s', (user_token,))
    existing_vote = cur.fetchone()
    if existing_vote:
        cur.close()
        conn.close()
        return jsonify({"message": "You have already voted!"}), 400
    
    cur.execute('INSERT INTO votes (user_token, option_id) VALUES (%s, %s)', (user_token, option_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Vote counted successfully!"})

# Get poll details
@app.route('/polls/<int:poll_id>', methods=['GET'])
def get_poll(poll_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection failed!"}), 500

    cur = conn.cursor()
    cur.execute('SELECT question FROM polls WHERE id = %s', (poll_id,))
    poll = cur.fetchone()
    if not poll:
        cur.close()
        conn.close()
        return jsonify({"error": "Poll not found"}), 404

    question = poll[0]
    cur.execute('SELECT id, option_text FROM options WHERE poll_id = %s', (poll_id,))
    options = [{"id": row[0], "option_text": row[1]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"question": question, "options": options})

# Admin route to view poll results
@app.route('/polls/<int:poll_id>/results', methods=['POST'])
def get_poll_results(poll_id):
    data = request.get_json()
    admin_password = data.get('password')
    if admin_password != ADMIN_PASSWORD:
        return jsonify({"message": "Unauthorized access!"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection failed!"}), 500

    cur = conn.cursor()
    cur.execute('SELECT question FROM polls WHERE id = %s', (poll_id,))
    poll = cur.fetchone()
    if not poll:
        cur.close()
        conn.close()
        return jsonify({"message": "Poll not found!"}), 404

    cur.execute(''' 
        SELECT option_text, COUNT(votes.id) AS vote_count
        FROM options
        LEFT JOIN votes ON options.id = votes.option_id
        WHERE options.poll_id = %s
        GROUP BY options.id
        ORDER BY vote_count DESC
    ''', (poll_id,))
    results = cur.fetchall()
    cur.close()
    conn.close()

    options = [{"option_text": row[0], "vote_count": row[1]} for row in results]
    winner = max(options, key=lambda x: x["vote_count"]) if options else None

    return jsonify({
        "poll_question": poll[0],
        "results": options,
        "winner": winner["option_text"] if winner else "No votes yet"
    })

# Main route to serve the frontend (if applicable)
@app.route('/')
def index():
    return render_template('index.html')


# Run the app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

