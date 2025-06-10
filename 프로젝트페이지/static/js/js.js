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
        <img src="${member.IMAGE_URL || 'https://via.placeholder.com/200x250?text=No+Image'}" alt="${member.HG_NM}">
      </div>
      <div class="product-info">
        <h3 class="product-title">${member.HG_NM}</h3>
        <p><b>정당:</b> ${member.POLY_NM || '정보 없음'}</p>
        <p><b>지역구:</b> ${member.ORIG_NM || '정보 없음'}</p>
        <p><b>성별:</b> ${member.SEX_GBN_NM || '정보 없음'}</p>
      </div>
    `;
    container.appendChild(card);
  });
}

function filterMembers() {
  const name = document.getElementById("name")?.value.trim() || "";
  const party = document.getElementById("party")?.value || "";
  const area = document.getElementById("area")?.value || "";
  const gender = document.getElementById("gender")?.value || "";

  // ✅ window.members 사용으로 통일
  const filtered = (window.members || []).filter(m => {
    return (
      (!name || (m.NAAS_NM && m.NAAS_NM.includes(name))) &&
      (!party || m.PLPT_NM === party) &&
      (!area || (m.ELECD_NM && m.ELECD_NM.includes(area))) &&
      (!gender || m.NTR_DIV === gender)
    );
  });

  currentPage = 1;
  displayMembers(filtered);
  renderPagination(filtered);
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
      <strong>${m.NAAS_NM}</strong> - ${m.POLY_NM || "소속 없음"}<br>
      지역구: ${m.ORIG_NM || "정보 없음"}<br>
      성별: ${m.SEX_GBN_NM || "정보 없음"}
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
