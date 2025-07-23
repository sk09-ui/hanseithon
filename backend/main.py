from flask import Flask, request, Response
import sqlite3
import json
import os
from flask_cors import CORS
import re

def extract_hashtags(text):
    return re.findall(r'#\w+', text)

app = Flask(__name__)
CORS(app)
DB_PATH = 'memos.db'

# DB 초기화 함수
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 메모 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL
            )
        ''')

        # 해시태그 테이블 (중복 방지용 UNIQUE)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hashtags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT UNIQUE NOT NULL
            )
        ''')

        # 메모-해시태그 연결 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memo_hashtags (
                memo_id INTEGER,
                hashtag_id INTEGER,
                FOREIGN KEY (memo_id) REFERENCES memos(id),
                FOREIGN KEY (hashtag_id) REFERENCES hashtags(id)
            )
        ''')

        conn.commit()


# JSON 응답 함수 (한글 깨짐 방지)
def json_response(data, status=200):
    return Response(
        response=json.dumps(data, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )

@app.route('/memos', methods=['GET'])
def get_memos():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, content FROM memos')
        rows = cursor.fetchall()
        memos = [{'id': row[0], 'content': row[1]} for row in rows]
    return json_response(memos)

@app.route('/memos', methods=['POST'])
def add_memo():
    data = request.get_json()
    content = data.get('content')

    if not content:
        return json_response({'error': '내용이 없습니다.'}, 400)

    hashtags = extract_hashtags(content)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 메모 저장
        cursor.execute('INSERT INTO memos (content) VALUES (?)', (content,))
        memo_id = cursor.lastrowid

        for tag in hashtags:
            # 중복 방지용: 이미 있으면 무시
            cursor.execute('INSERT OR IGNORE INTO hashtags (tag) VALUES (?)', (tag,))
            # ID 조회
            cursor.execute('SELECT id FROM hashtags WHERE tag = ?', (tag,))
            hashtag_id = cursor.fetchone()[0]

            # 연결 테이블에 저장
            cursor.execute(
                'INSERT INTO memo_hashtags (memo_id, hashtag_id) VALUES (?, ?)',
                (memo_id, hashtag_id)
            )

        conn.commit()

    return json_response({'id': memo_id, 'content': content, 'hashtags': hashtags}, 201)

@app.route('/memos/<int:memo_id>', methods=['DELETE'])
def delete_memo(memo_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, content FROM memos WHERE id = ?', (memo_id,))
        row = cursor.fetchone()
        if row:
            cursor.execute('DELETE FROM memos WHERE id = ?', (memo_id,))
            conn.commit()
            return json_response({'deleted': {'id': row[0], 'content': row[1]}})
        else:
            return json_response({'error': '존재하지 않는 메모입니다.'}, 404)
        


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
