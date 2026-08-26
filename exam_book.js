/* 기출 회차 조립기 — exam/ 안의 회차 파일을 모아 한 배열로 돌려준다.
 *
 * 회차마다 파일을 따로 두는 이유: 여러 세션이 동시에 전사할 때 한 파일이면
 * 서로 덮어쓴다. 파일이 나뉘어 있으면 세션끼리 겹칠 일이 없고,
 * '아직 파일이 없는 회차'를 고르는 것만으로 찜하기가 된다.
 *
 * 이 파일은 build_lock.py(node)만 읽는다. 브라우저는 bank.enc 만 본다.
 */
const fs = require('fs');
const path = require('path');

const DIR = path.join(__dirname, 'exam');
const EXAMS = [];

if (fs.existsSync(DIR)) {
  fs.readdirSync(DIR)
    .filter(f => f.endsWith('.js'))
    .forEach(f => {
      const e = require(path.join(DIR, f));
      if (e && Array.isArray(e.qs) && e.qs.length) EXAMS.push(e);
      else console.error('  ⚠️ 건너뜀(문항 없음): exam/' + f);
    });
  // 연도 → 회차 순으로 정렬
  EXAMS.sort((a, b) => (a.year - b.year) || (a.round - b.round));
}

module.exports = EXAMS;
