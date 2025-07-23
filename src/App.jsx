import React, { useState, useEffect } from 'react';

const API_BASE = 'http://127.0.0.1:5000';

function App() {
  const [memos, setMemos] = useState([]);
  const [content, setContent] = useState('');
  const [password, setPassword] = useState('');
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteId, setDeleteId] = useState(null);
  const [categories, setCategories] = useState({});
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [categoryMemos, setCategoryMemos] = useState([]);

  // 전체 메모 가져오기
  const fetchMemos = async () => {
    const res = await fetch(`${API_BASE}/memos`);
    const data = await res.json();
    setMemos(data);
  };

  // 카테고리 목록 + 해시태그 가져오기
  const fetchCategories = async () => {
    const res = await fetch(`${API_BASE}/category`);
    const data = await res.json();
    setCategories(data.categories);
  };

  // 카테고리별 메모 가져오기
  const fetchCategoryMemos = async (category) => {
    const res = await fetch(`${API_BASE}/category/${category}`);
    if (res.ok) {
      const data = await res.json();
      setCategoryMemos(data);
      setSelectedCategory(category);
    } else {
      alert('존재하지 않는 카테고리입니다.');
    }
  };

  // 메모 추가
  // 저장 버튼 이벤트 핸들러
  const handleAddMemo = async () => {
    if (!content || !password) {
      alert('내용과 비밀번호를 모두 입력하세요.');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/memos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, password }),
      });

      if (!res.ok) {
        const err = await res.json();
        alert(`저장 실패: ${err.error}`);
        return;
      }

      const newMemo = await res.json();

      setMemos(prev => [...prev, newMemo]);
      setContent('');
      setPassword('');

      fetchCategories();
      if (selectedCategory) fetchCategoryMemos(selectedCategory);

    } catch (error) {
      alert('서버 연결 실패');
      console.error(error);
    }
  };


  // 메모 삭제
  const handleDeleteMemo = async (id) => {
    const pwd = prompt('삭제할 메모 비밀번호를 입력하세요.');
    if (!pwd) return;

    const res = await fetch(`${API_BASE}/memos/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pwd }),
    });
    if (res.ok) {
      fetchMemos();
      fetchCategories();
      if (selectedCategory) fetchCategoryMemos(selectedCategory);
    } else {
      const err = await res.json();
      alert(err.error);
    }
  };

  // 초기 데이터 로드
  useEffect(() => {
    fetchMemos();
    fetchCategories();
  }, []);

  return (
    <div style={{ maxWidth: 600, margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <h1>메모장</h1>

      <div style={{ marginBottom: 20 }}>
        <h2>메모 작성</h2>
        <textarea
          rows={3}
          placeholder="내용을 입력하세요. 해시태그는 #붙여서 작성"
          value={content}
          onChange={e => setContent(e.target.value)}
          style={{ width: '100%' }}
        />
        <input
          type="password"
          placeholder="비밀번호"
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ width: '100%', marginTop: 8 }}
        />
        <button onClick={handleAddMemo} style={{ marginTop: 8 }}>
          저장
        </button>
      </div>

      <div style={{ marginBottom: 20 }}>
        <h2>카테고리 목록</h2>
        {Object.keys(categories).length === 0 && <p>카테고리가 없습니다.</p>}
        <ul>
          {Object.entries(categories).map(([category, tags]) => (
            <li key={category}>
              <button onClick={() => fetchCategoryMemos(category)}>{category}</button>
              : {tags.join(', ')}
            </li>
          ))}
        </ul>
        {selectedCategory && (
          <>
            <h3>{selectedCategory} 카테고리 메모</h3>
            {categoryMemos.length === 0 && <p>해당 카테고리에 메모가 없습니다.</p>}
            <ul>
              {categoryMemos.map(memo => (
                <li key={memo.id}>
                  {memo.content}
                  <button
                    onClick={() => handleDeleteMemo(memo.id)}
                    style={{ marginLeft: 10, color: 'red' }}
                  >
                    삭제
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div>
        <h2>전체 메모 목록</h2>
        {memos.length === 0 && <p>메모가 없습니다.</p>}
        <ul>
          {memos.map(memo => (
            <li key={memo.id}>
              {memo.content}
              <button
                onClick={() => handleDeleteMemo(memo.id)}
                style={{ marginLeft: 10, color: 'red' }}
              >
                삭제
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;
