import React, { useState, useEffect } from 'react';
import './index.css';

const API_BASE = 'http://127.0.0.1:5000';

function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [memos, setMemos] = useState([]);
  const [content, setContent] = useState('');
  const [password, setPassword] = useState('');
  const [categories, setCategories] = useState({});
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [categoryMemos, setCategoryMemos] = useState([]);

  const [deleteMemoId, setDeleteMemoId] = useState(null);
  const [deletePwd, setDeletePwd] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editMemoId, setEditMemoId] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [editPassword, setEditPassword] = useState('');

  useEffect(() => {
    document.title = "Inought ✍️";  // 원하는 제목
  }, []);

  const openEditModal = (memo) => {
    setEditMemoId(memo.id);
    setEditContent(memo.content);
    setEditPassword('');
  };

  const closeEditModal = () => {
    setEditMemoId(null);
    setEditContent('');
    setEditPassword('');
  };
  const handleEditMemo = async () => {
    if (!editContent || !editPassword) {
      alert('내용과 비밀번호를 모두 입력해주세요.');
      return;
    }

    try {
      const hashed = await hashPassword(editPassword); // SHA-256 해시
      const res = await fetch(`${API_BASE}/memos/${editMemoId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: editContent,
          password: hashed
        })
      });

      const data = await res.json();

      if (res.ok) {
        alert('메모가 수정되었습니다.');
        fetchMemos(); // 전체 메모 갱신
        fetchCategories(); // 카테고리 메모도 갱신
        if (selectedCategory) fetchCategoryMemos(selectedCategory);
        closeEditModal();
      } else {
        alert(data.error);
      }
    } catch (error) {
      console.error('수정 실패:', error);
      alert('서버 오류');
    }
  };


  // SHA-256 해시 함수
  async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  }

  // 메모 가져오기
  const fetchMemos = async () => {
    const res = await fetch(`${API_BASE}/memos`);
    const data = await res.json();
    setMemos(data);
  };

  // 카테고리 목록
  const fetchCategories = async () => {
    const res = await fetch(`${API_BASE}/category`);
    const data = await res.json();
    setCategories(data.categories);
  };

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

  const handleCategoryClick = (category) => {
    fetchCategoryMemos(category);
  };

  // 메모 추가
  const handleAddMemo = async (e) => {
    e.preventDefault();
    if (!content || !password) {
      alert('내용과 비밀번호를 모두 입력하세요.');
      return;
    }

    try {
      const hashed = await hashPassword(password); // 해싱 처리
      const res = await fetch(`${API_BASE}/memos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, password: hashed }),
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

  // 삭제 버튼 누르면 모달
  const openDeleteModal = (id) => {
    setDeleteMemoId(id);
    setDeletePwd('');
    setShowDeleteModal(true);
  };

  // 삭제 모달 확인
  const handleDeleteMemo = async () => {
    if (!deletePwd) {
      alert('비밀번호를 입력하세요.');
      return;
    }

    try {
      const hashedPwd = await hashPassword(deletePwd);
      const res = await fetch(`${API_BASE}/memos/${deleteMemoId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: hashedPwd }),
      });

      if (res.ok) {
        setShowDeleteModal(false);
        setDeleteMemoId(null);
        setDeletePwd('');
        fetchMemos();
        fetchCategories();
        if (selectedCategory) fetchCategoryMemos(selectedCategory);
      } else {
        const err = await res.json();
        alert(err.error);
      }
    } catch (error) {
      alert('서버 연결 실패');
      console.error(error);
    }
  };

  const cancelDelete = () => {
    setShowDeleteModal(false);
    setDeleteMemoId(null);
    setDeletePwd('');
  };

  useEffect(() => {
    fetchMemos();
    fetchCategories();
  }, []);

  return (
    <div className={`app-container ${isDarkMode ? 'dark-mode' : ''}`}>
      <nav className="navbar">
        <div className="navbar-logo">♾️ <span>inought</span> </div>
        <button onClick={() => setIsDarkMode(prev => !prev)}>
          {isDarkMode ? '🌞 Light' : '🌙 Dark'}
        </button>
      </nav>
      {/* 왼쪽 패널 */}
      <div className="left-panel" >
        <h2>📂 카테고리</h2>
        {Object.entries(categories).map(([cat, tags]) => (
          <button key={cat} onClick={() => handleCategoryClick(cat)}>
            {cat}
          </button>
        ))}

        {selectedCategory && (
          <>
            <h3>{selectedCategory} 관련 메모</h3>
            {categoryMemos.map((memo) => (
              <div className="memo-item" key={memo.id}>
                <span>{memo.content}</span>
              </div>
            ))}
          </>
        )}
      </div>


      {/* 중앙 패널 */}
      <div className="center-panel">
        <h2>📝 메모 작성</h2>
        <form onSubmit={handleAddMemo}>
          <textarea
            style={{ width: '577px', height: '80px' }}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="내용를 입력하세요..."
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="비밀번호"
          />
          <button type="submit" style={{ marginTop: '5px', }}>추가</button>
        </form>
        <div className="category-guide">
          <h3>카테고리 안내</h3>
          {Object.entries(categories).map(([cat, tags]) => (
            <div key={cat} className="category-info">
              <strong>{cat}:</strong> {tags.join(', ')}
            </div>
          ))}
        </div>
      </div>

      {/* 오른쪽 패널 */}
      <div className="right-panel">
        <h2>📋 전체 메모</h2>
        {memos.map((memo) => (
          <div className="memo-item" key={memo.id}>
            <span>{memo.content}</span>
            <button onClick={() => openEditModal(memo)}>✏️</button>
            <button className="delete-button" onClick={() => openDeleteModal(memo.id)}>🗑️</button>
          </div>
        ))}
      </div>

      {/* 삭제 모달 */}
      {
        showDeleteModal && (
          <div className="modal-backdrop" onClick={cancelDelete}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h3>삭제할 메모 비밀번호를 입력하세요.</h3>
              <input
                type="password"
                value={deletePwd}
                onChange={(e) => setDeletePwd(e.target.value)}
                placeholder="비밀번호"
                autoFocus
              />
              <div className="modal-buttons">
                <button onClick={handleDeleteMemo}>확인</button>
                <button onClick={cancelDelete}>취소</button>
              </div>
            </div>
          </div>
        )
      }

      {
        editMemoId && (
          <div className="modal-backdrop" onClick={closeEditModal}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
              <h3>메모 수정</h3>
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
              />
              <input
                type="password"
                value={editPassword}
                onChange={(e) => setEditPassword(e.target.value)}
                placeholder="비밀번호 입력"
              />
              <div className="modal-buttons">
                <button onClick={handleEditMemo}>수정</button>
                <button onClick={closeEditModal}>취소</button>
              </div>
            </div>
          </div>
        )
      }
    </div >
  );
}

export default App;
