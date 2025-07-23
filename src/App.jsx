import React, { useState, useEffect } from 'react';
import './index.css';

const API_BASE = 'http://localhost:5000';

function App() {
  const [memos, setMemos] = useState([]);
  const [newMemo, setNewMemo] = useState('');

  // 메모 전체 가져오기
  const fetchMemos = async () => {
    const res = await fetch(`${API_BASE}/memos`);
    const data = await res.json();
    setMemos(data);
  };

  useEffect(() => {
    fetchMemos();
  }, []);

  // 메모 추가
  const addMemo = async () => {
    if (!newMemo.trim()) return;

    const res = await fetch(`${API_BASE}/memos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newMemo }),
    });

    if (res.ok) {
      setNewMemo('');
      fetchMemos(); // 다시 불러오기
    }
  };

  // 메모 삭제
  const deleteMemo = async (id) => {
    await fetch(`${API_BASE}/memos/${id}`, {
      method: 'DELETE',
    });
    fetchMemos();
  };

  return (<>
    <div id='search'>
      <h1>🔍 검색</h1>
      <input type="text" />
      <button>검색</button>
    </div>

    <div id='add_memos'>
      <h1>📝 메모장</h1>
      <input
        type="text"
        value={newMemo}
        onChange={(e) => setNewMemo(e.target.value)}
        placeholder="새 메모 작성"
        style={{ flex: 1, padding: '0.5rem' }}
      />
      <button onClick={addMemo}>추가</button>
      <ul>
        {memos.map((memo) => (
          <li key={memo.id} style={{ marginBottom: '0.5rem' }}>
            {memo.content}
            <button onClick={() => deleteMemo(memo.id)} style={{ marginLeft: '1rem' }}>
              ❌ 삭제
            </button>
          </li>
        ))}
      </ul>
    </div>
  </>
  );
}

export default App;