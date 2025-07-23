from flask import Flask, request, Response
import sqlite3
import json
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB_PATH = 'memos.db'

def json_response(data, status=200):
    return Response(
        response=json.dumps(data, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )

def extract_hashtags(text):
    raw_tags = re.findall(r'#\S+', text)
    valid_tags = [tag for tag in raw_tags if re.match(r'^#[\w가-힣]+$', tag)]
    return valid_tags

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

        conn.commit()

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
    password = data.get('password')  # 클라이언트가 SHA-256 해시된 비밀번호 보낸다고 가정

    if not content or not password:
        return json_response({'error': '내용과 비밀번호를 모두 입력하세요.'}, 400)

    hashtags = extract_hashtags(content)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 해시된 비밀번호 그대로 저장
        cursor.execute('INSERT INTO memos (content, password) VALUES (?, ?)', (content, password))
        memo_id = cursor.lastrowid

        for tag in hashtags:
            cursor.execute('INSERT OR IGNORE INTO hashtags (tag) VALUES (?)', (tag,))
            cursor.execute('SELECT id FROM hashtags WHERE tag = ?', (tag,))
            hashtag_id = cursor.fetchone()[0]

            cursor.execute(
                'INSERT INTO memo_hashtags (memo_id, hashtag_id) VALUES (?, ?)',
                (memo_id, hashtag_id)
            )

        conn.commit()

    return json_response({'id': memo_id, 'content': content, 'hashtags': hashtags}, 201)

@app.route('/memos/<int:memo_id>', methods=['DELETE'])
def delete_memo(memo_id):
    data = request.get_json()
    password = data.get('password')  # 클라이언트가 SHA-256 해시된 비밀번호 보낸다고 가정

    if not password:
        return json_response({'error': '비밀번호가 필요합니다.'}, 400)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM memos WHERE id = ?', (memo_id,))
        row = cursor.fetchone()

        if not row:
            return json_response({'error': '존재하지 않는 메모입니다.'}, 404)

        stored_password = row[0]

        if stored_password != password:
            return json_response({'error': '비밀번호가 일치하지 않습니다.'}, 403)

        cursor.execute('DELETE FROM memos WHERE id = ?', (memo_id,))
        conn.commit()

    return json_response({'message': '삭제되었습니다.'})

CATEGORIES = {
    "기쁨 😊": ["#만족감", "#사랑", "#행복", "#희망", "#감사함", "#흥분", "#뿌듯함", "#안도감"],
    "슬픔 😢": ["#외로움", "#우울감", "#실망", "#죄책감", "#상실감", "#후회", "#연민"],
    "분노 😡": ["#짜증", "#분개", "#질투", "#원한", "#억울함", "#분노폭발"],
    "공포 😨": ["#불안", "#긴장감", "#공황", "#의심", "#두려움", "#불확실함"],
    "혐오 🤢": ["#역겨움", "#혐오감", "#편견", "#경멸"],
    "놀람 😲": ["#경이로움", "#당황", "#충격"]
}

@app.route('/category', methods=['GET'])
def get_categories():
    return json_response({'categories': CATEGORIES})

@app.route('/category/<category>', methods=['GET'])
def get_category_memos(category):
    tags = CATEGORIES.get(category)
    if not tags:
        return json_response({'error': '존재하지 않는 카테고리입니다.'}, 404)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, m.content FROM memos m
            JOIN memo_hashtags mh ON m.id = mh.memo_id
            JOIN hashtags h ON mh.hashtag_id = h.id
            WHERE h.tag IN ({})
            GROUP BY m.id
        '''.format(','.join('?' for _ in tags)), tags)
        rows = cursor.fetchall()

        memos = []
        for row in rows:
            content_without_hashtags = re.sub(r'#\w+', '', row[1]).strip()
            memos.append({'id': row[0], 'content': content_without_hashtags})

    return json_response(memos)

@app.route('/memos/<int:memo_id>', methods=['PUT'])
def update_memo(memo_id):
    data = request.get_json()
    new_content = data.get('content')
    password = data.get('password')  # SHA-256으로 해시된 비밀번호

    if not new_content or not password:
        return json_response({'error': '내용과 비밀번호가 필요합니다.'}, 400)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 기존 비밀번호 확인
        cursor.execute('SELECT password FROM memos WHERE id = ?', (memo_id,))
        row = cursor.fetchone()

        if not row:
            return json_response({'error': '존재하지 않는 메모입니다.'}, 404)

        stored_password = row[0]

        if stored_password != password:
            return json_response({'error': '비밀번호가 일치하지 않습니다.'}, 403)

        # 기존 해시태그 관계 제거
        cursor.execute('DELETE FROM memo_hashtags WHERE memo_id = ?', (memo_id,))

        # 메모 내용 업데이트
        cursor.execute('UPDATE memos SET content = ? WHERE id = ?', (new_content, memo_id))

        # 새로운 해시태그 추출 후 저장
        new_tags = extract_hashtags(new_content)
        for tag in new_tags:
            cursor.execute('INSERT OR IGNORE INTO hashtags (tag) VALUES (?)', (tag,))
            cursor.execute('SELECT id FROM hashtags WHERE tag = ?', (tag,))
            hashtag_id = cursor.fetchone()[0]
            cursor.execute('INSERT INTO memo_hashtags (memo_id, hashtag_id) VALUES (?, ?)', (memo_id, hashtag_id))

        conn.commit()

    return json_response({'message': '메모가 성공적으로 수정되었습니다.', 'id': memo_id, 'content': new_content})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
