let currentPage = 1;
const itemsPerPage = 10;

document.addEventListener('DOMContentLoaded', () => {
  // 카드 생성
  if (document.getElementById('memberContainer')) {
    createMemberCards(window.members);
  }
  
  // 검색 페이지 초기화
  if (document.getElementById('resultContainer')) {
    displayMembers();
    renderPagination();
  }
});

function createMemberCards(list = window.members || []) {
  const container = document.getElementById('memberContainer');
  if (!container) return;
  container.innerHTML = '';
  list.forEach(member => {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
      <div class="product-image">
        <img src="${member.NAAS_PIC || 'https://via.placeholder.com/200x250?text=No+Image'}" alt="${member.NAAS_NM}">
      </div>
      <div class="product-info">
        <h3 class="product-title">${member.NAAS_NM}</h3>
      </div>
    `;
    // 카드 클릭 시 상세 정보 모달 띄우기
    card.onclick = () => showMemberModal(member);
    container.appendChild(card);
  });
}
function showMemberModal(member) {
  const modal = document.getElementById('memberModal');
  const content = document.getElementById('modalContent');
  content.innerHTML = `
    <span id="closeModal" style="position:absolute; top:10px; right:18px; font-size:2rem; cursor:pointer;">&times;</span>
    <div style="display:flex; gap:24px; align-items:center;">
      <img src="${member.NAAS_PIC || 'https://via.placeholder.com/200x250?text=No+Image'}" 
           alt="${member.NAAS_NM}" style="width:120px; height:160px; object-fit:cover; border-radius:4px;">
      <div>
        <h2 style="margin-bottom:10px;">${member.NAAS_NM}</h2>
        <p><b>정당:</b> ${member.PLPT_NM || '정보 없음'}</p>
        <p><b>지역구:</b> ${member.ELECD_NM || '정보 없음'}</p>
        <p><b>성별:</b> ${member.NTR_DIV || '정보 없음'}</p>
        <!-- 필요시 더 많은 정보 추가 -->
      </div>
    </div>
  `;
  modal.style.display = 'flex';

  // 닫기 버튼 동작
  document.getElementById('closeModal').onclick = () => {
    modal.style.display = 'none';
  };
  // 모달 바깥 클릭 시 닫힘
  modal.onclick = (e) => {
    if (e.target === modal) modal.style.display = 'none';
  };
}





function filterMembers() {
  const name = document.getElementById("name")?.value.trim() || "";
  const party = document.getElementById("party")?.value || "";
  const area = document.getElementById("area")?.value || "";
  const gender = document.getElementById("gender")?.value || "";

  // ✅ window.members 사용으로 통일
 const filtered = (window.members || []).filter(m => {
  // 현재 정당만 추출
  const parties = (m.PLPT_NM || '').split('/').map(s => s.trim()).filter(Boolean);
  const currentParty = parties.length ? parties[parties.length - 1] : '';
  return (
    (!name || (m.NAAS_NM && m.NAAS_NM.includes(name))) &&
    (!party || currentParty === party) &&
    (!area || (m.ELECD_NM && m.ELECD_NM.includes(area))) &&
    (!gender || m.NTR_DIV === gender)
  );
});


  currentPage = 1;
  displayMembers(filtered);
  renderPagination(filtered);
}
function getMultipleParties() {
  const params = new URLSearchParams(location.search);
  const parties = params.getAll('party');
  return parties.map(p => decodeURIComponent(p));
}

function resetFilters() {
  const nameInput = document.getElementById("name");
  const partyInput = document.getElementById("party");
  const areaInput = document.getElementById("area");
  const genderInput = document.getElementById("gender");
  
  if (nameInput) nameInput.value = "";
  if (partyInput) partyInput.value = "";
  if (areaInput) areaInput.value = "";
  if (genderInput) genderInput.value = "";
  
  currentPage = 1;
  displayMembers();
  renderPagination();
}

function displayMembers(list = window.members || []) {
  const container = document.getElementById("resultContainer");
  if (!container) return;
  
  container.innerHTML = "";

  const start = (currentPage - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  const pageMembers = list.slice(start, end);

  if (!pageMembers.length) {
    container.innerHTML = "<p>검색 결과가 없습니다.</p>";
    return;
  }

  pageMembers.forEach(m => {
    const card = document.createElement("div");
    card.style.border = "1px solid #ccc";
    card.style.padding = "10px";
    card.style.marginBottom = "10px";
    card.style.borderRadius = "8px";
    card.style.backgroundColor = "white";
    card.innerHTML = `
      <strong>${m.NAAS_NM}</strong> - ${m.PLPT_NM || "소속 없음"}<br>
      지역구: ${m.ELECD_NM || "정보 없음"}<br>
      성별: ${m.NTR_DIV || "정보 없음"}
    `;
    container.appendChild(card);
  });
}

function renderPagination(list = window.members || []) {
  const pagination = document.getElementById("pagination");
  if (!pagination) return;
  
  pagination.innerHTML = "";

  const totalItems = list.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  if (totalPages <= 1) return;

  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement("button");
    btn.textContent = i;
    btn.style.margin = "0 3px";
    btn.style.padding = "4px 10px";
    btn.style.borderRadius = "4px";
    btn.style.border = "1px solid #bbb";
    btn.style.background = (i === currentPage) ? "#007bff" : "#fff";
    btn.style.color = (i === currentPage) ? "#fff" : "#222";
    btn.onclick = () => {
      currentPage = i;
      displayMembers(list);
      renderPagination(list);
    };
    pagination.appendChild(btn);
  }
}
