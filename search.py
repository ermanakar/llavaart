import sqlite3
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

DATABASE = 'app.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

@app.route('/api/search', methods=['GET'])
def search_images():
    query = request.args.get('query', '')
    conn = get_db()
    cursor = conn.cursor()
    
    # Enhanced search across multiple columns
    search_query = f"%{query}%"
    cursor.execute('''
        SELECT * FROM iterations 
        WHERE description LIKE ? 
        OR title LIKE ? 
        OR tags LIKE ? 
        OR short_description LIKE ?
    ''', (search_query, search_query, search_query, search_query))
    
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        result = {
            'id': row[0],
            'job_id': row[1],
            'iteration_number': row[2],
            'timestamp': row[3],
            'description': row[4],
            'image_url': row[5],
            'revised_prompt': row[6],
            'title': row[7],
            'tags': row[8],
            'short_description': row[9]
        }
        
        results.append(result)

    return jsonify(results)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(port=5001)
