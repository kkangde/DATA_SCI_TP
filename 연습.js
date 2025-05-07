let members = [];

// 페이지 로드 시 실행
window.onload = () => {
  fetchMembers();

  // 필터 영역 가로 정렬 스타일 적용
  const container = document.getElementById("filterContainer");
  container.style.display = "flex";
  container.style.flexWrap = "wrap";
  container.style.gap = "10px";
  container.style.alignItems = "center";

  const items = container.querySelectorAll(".filter-item");
  items.forEach(item => {
    item.style.display = "inline-flex";
    item.style.alignItems = "center";
    item.style.gap = "5px";
  });
};

// API에서 국회의원 데이터 가져오기
async function fetchMembers() {
  const apiKey = "f387f85a7e104ed4834c91779eef1249";
  const url = `https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER?KEY=${apiKey}&Type=json`;

  try {
    const response = await fetch(url);
    const data = await response.json();
    members = data?.['ALLNAMEMBER'][1]?.row || [];

    populateFilters(members);
    displayMembers(members);
  } catch (error) {
    console.error("데이터 불러오기 실패:", error);
    document.getElementById("memberList").innerText = "API 호출 실패 또는 인증 오류";
  }
}

// ELECD_NM에서 지역(광역시도) 추출
function getRegionFromELECD_NM(elecd_nm) {
  return elecd_nm?.split(" ")[0] || "";
}

// 필터 옵션 채우기
function populateFilters(data) {
  const regionSet = new Set();
  const genderSet = new Set();
  const partySet = new Set();

  data.forEach(m => {
    const wideRegion = getRegionFromELECD_NM(m.ELECD_NM);
    if (wideRegion) regionSet.add(wideRegion);

    genderSet.add(m.NTR_DIV);
    partySet.add(...m.PLPT_NM.split(",").map(s => s.trim()));
  });

  fillSelect("regionFilter", [...regionSet]);
  fillSelect("genderFilter", [...genderSet]);
  fillSelect("partyFilter", [...partySet]);
}

// select 요소에 옵션 추가
function fillSelect(id, options) {
  const select = document.getElementById(id);
  options.sort().forEach(opt => {
    const option = document.createElement("option");
    option.value = opt;
    option.textContent = opt;
    select.appendChild(option);
  });
}

// 필터 적용
function applyFilters() {
  const name = document.getElementById('nameFilter').value.toLowerCase();
  const region = document.getElementById('regionFilter').value;
  const gender = document.getElementById('genderFilter').value;
  const party = document.getElementById('partyFilter').value;

  const filtered = members.filter(m =>
    (!name || m.NAAS_NM.toLowerCase().includes(name)) &&
    (!region || getRegionFromELECD_NM(m.ELECD_NM) === region) &&
    (!gender || m.NTR_DIV === gender) &&
    (!party || m.PLPT_NM.split(",").some(p => p.trim() === party))
  );

  displayMembers(filtered);
}

// 국회의원 목록 표시
function displayMembers(list) {
  const container = document.getElementById("memberList");
  container.innerHTML = "";

  if (list.length === 0) {
    container.innerHTML = "<p>조건에 맞는 의원이 없습니다.</p>";
    return;
  }

  list.forEach(m => {
    container.innerHTML += `
      <div class="member">
        <strong>${m.NAAS_NM}</strong> (${m.NTR_DIV})<br/>
        지역: ${m.ELECD_NM}<br/>
        정당: ${m.PLPT_NM}
      </div>
    `;
  });
}
