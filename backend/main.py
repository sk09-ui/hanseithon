from flask import Flask, request, Response
import sqlite3
import json
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) 

DB_PATH = 'memos.db'

# 미리 정의된 해시태그 기반 카테고리 분류
CATEGORY_TAGS = {
    '기쁨': ['행복', '신남', '최고'],
    '화남': ['짜증나', '화나', '빡친다'],
    '슬픔': ['눈물', '슬퍼', '우울하다']
}

# 해시태그 추출 함수
def extract_hashtags(text):
    return re.findall(r'#\w+', text)

# 해시태그 기반 카테고리 자동 분류
def categorize_tags(hashtags):
    result = set()
    for category, keywords in CATEGORY_TAGS.items():
        for tag in hashtags:
            for keyword in keywords:
                if keyword in tag:
                    result.add(category)
    return list(result)

# JSON 응답 함수
def json_response(data, status=200):
    return Response(
        response=json.dumps(data, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )

# DB 초기화
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hashtags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT UNIQUE NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memo_hashtags (
                memo_id INTEGER,
                hashtag_id INTEGER,
                FOREIGN KEY (memo_id) REFERENCES memos(id),
                FOREIGN KEY (hashtag_id) REFERENCES hashtags(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memo_categories (
                memo_id INTEGER,
                category TEXT,
                FOREIGN KEY (memo_id) REFERENCES memos(id)
            )
        ''')

        conn.commit()

# 메모 전체 조회
@app.route('/memos', methods=['GET'])
def get_memos():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, content FROM memos')
        rows = cursor.fetchall()
        memos = [{'id': row[0], 'content': row[1]} for row in rows]
    return json_response(memos)

# 메모 추가 (비밀번호 포함)
@app.route('/memos', methods=['POST'])
def add_memo():
    data = request.get_json()
    content = data.get('content')
    password = data.get('password')

    if not content:
        return json_response({'error': '내용이 없습니다.'}, 400)
    if not password:
        return json_response({'error': '비밀번호를 입력하세요.'}, 400)

    hashtags = extract_hashtags(content)
    tags_without_hash = [tag.lstrip('#') for tag in hashtags]
    categories = categorize_tags(tags_without_hash)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 메모 저장 (비밀번호 포함)
        cursor.execute('INSERT INTO memos (content, password) VALUES (?, ?)', (content, password))
        memo_id = cursor.lastrowid

        # 해시태그 저장 및 연결
        for tag in hashtags:
            cursor.execute('INSERT OR IGNORE INTO hashtags (tag) VALUES (?)', (tag,))
            cursor.execute('SELECT id FROM hashtags WHERE tag = ?', (tag,))
            hashtag_id = cursor.fetchone()[0]
            cursor.execute(
                'INSERT INTO memo_hashtags (memo_id, hashtag_id) VALUES (?, ?)',
                (memo_id, hashtag_id)
            )

        # 카테고리 저장
        for category in categories:
            cursor.execute(
                'INSERT INTO memo_categories (memo_id, category) VALUES (?, ?)',
                (memo_id, category)
            )

        conn.commit()

    return json_response({
        'id': memo_id,
        'content': content,
        'hashtags': hashtags,
        'categories': categories
    }, 201)

# 비밀번호 검증 후 메모 삭제
@app.route('/memos/<int:memo_id>', methods=['DELETE'])
def delete_memo(memo_id):
    data = request.get_json()
    password = data.get('password')

    if not password:
        return json_response({'error': '비밀번호를 입력하세요.'}, 400)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password, content FROM memos WHERE id = ?', (memo_id,))
        row = cursor.fetchone()
        if not row:
            return json_response({'error': '존재하지 않는 메모입니다.'}, 404)

        stored_password, content = row
        if password != stored_password:
            return json_response({'error': '비밀번호가 틀렸습니다.'}, 403)

        cursor.execute('DELETE FROM memos WHERE id = ?', (memo_id,))
        # 연결된 해시태그 및 카테고리 데이터도 삭제 (선택사항)
        cursor.execute('DELETE FROM memo_hashtags WHERE memo_id = ?', (memo_id,))
        cursor.execute('DELETE FROM memo_categories WHERE memo_id = ?', (memo_id,))
        conn.commit()

        return json_response({'deleted': {'id': memo_id, 'content': content}})

# 카테고리 목록 + 해당 카테고리 해시태그 반환
@app.route('/category', methods=['GET'])
def get_all_categories_with_tags():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM memo_categories')
        rows = cursor.fetchall()
        db_categories = set(row[0] for row in rows)

    filtered_categories = {k: v for k, v in CATEGORY_TAGS.items() if k in db_categories}

    return json_response({'categories': filtered_categories})

# 카테고리별 메모 조회
@app.route('/category/<category>', methods=['GET'])
def get_memos_by_category(category):
    if category not in CATEGORY_TAGS:
        return json_response({'error': '존재하지 않는 카테고리입니다.'}, 400)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT memos.id, memos.content
            FROM memos
            JOIN memo_categories ON memos.id = memo_categories.memo_id
            WHERE memo_categories.category = ?
        ''', (category,))
        rows = cursor.fetchall()
        result = [{'id': row[0], 'content': row[1]} for row in rows]

    return json_response(result)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
