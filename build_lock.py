# 교재 적중예상문제(bank_book.js) -> 암호화(bank.enc)
#
#   python build_lock.py --pw <교사용 암호>
#
# 왜 이렇게 하나:
#   정적 호스팅(GitHub Pages)에서는 "화면에 비밀번호 입력칸"을 두어도 보호가 전혀 안 된다.
#   데이터 .js 파일 주소를 직접 치면 그대로 받아지기 때문이다.
#   그래서 파일 자체를 AES-GCM 으로 실제 암호화해서 올리고, 브라우저에서 WebCrypto 로 푼다.
#
# 암호가 두 종류인 이유 (수업용):
#   교사용 - 문구형, 만료 없음. 열면 그 주 학생 코드가 화면에 나온다.
#   학생용 - 8자리 숫자, 그 주 월요일 ~ 다음 월요일 7일만.
#   본문은 임의의 내용키(CK)로 한 번 암호화하고, CK 를 암호마다 따로 감싼다.
#   감싼 것들은 순서를 섞어 어느 것이 교사용인지 알 수 없다.
#   기간은 암호문 '안에' 들어 있어 화면이나 코드를 고쳐도 넘길 수 없다.
#
#   시크릿·기준일·접두어는 _weekly/secret.json 에 모아 두고 모든 도구가 함께 쓴다.
#   그래서 어느 도구에서든 같은 8자리가 통하고, 다시 빌드해도 코드가 바뀌지 않는다.
#
# 주의: 평문 bank_book.js 는 .gitignore 에 있다. 절대 커밋하지 말 것.
#       암호를 이 스크립트에 적어 두지 말 것 - 공개 저장소에 그대로 남는다.
import io, os, re, json, gzip, base64, argparse, sys, secrets
from datetime import date
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_weekly"))
import weekly                                   # 도구 공용 주간 코드
OUT = os.path.join(HERE, "bank.enc")
ITER = 200_000


def extract_json():
    """문항(bank_book.js) · 개념(concept_book.js) · 기출(exam_book.js)을
    node 로 평가해 한 덩어리 JSON 으로 만든다.

    셋을 하나의 payload 로 묶는 이유 — 잠금은 하나뿐인데 파일을 나누면
    암호문도 둘이 되고, 다시 빌드할 때 한쪽만 올라가는 사고가 난다."""
    import subprocess, tempfile
    driver = (
        "const bank = require('./bank_book.js');\n"
        "const concept = require('./concept_book.js');\n"
        "const exam = require('./exam_book.js');\n"
        "process.stdout.write(JSON.stringify({v:1, bank:bank, concept:concept, exam:exam}));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".js", dir=HERE, delete=False, encoding="utf-8") as f:
        f.write(driver)
        tmp = f.name
    try:
        r = subprocess.run(["node", tmp], capture_output=True, text=True,
                           encoding="utf-8", cwd=HERE)
        if r.returncode:
            raise SystemExit("node 평가 실패:\n" + r.stderr)
        return r.stdout
    finally:
        os.remove(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pw", required=True, help="교사용 암호 (만료 없음)")
    a = ap.parse_args()

    cfg = weekly.load()
    start = date.fromisoformat(cfg["epoch"])
    nweeks = cfg["weeks"]

    payload = extract_json()
    data = json.loads(payload)
    items = data["bank"]
    concept = data["concept"]
    exams = data.get("exam") or []
    raw = payload.encode("utf-8")
    gz = gzip.compress(raw, 9)

    # 1) 본문을 임의의 내용키(CK)로 한 번만 암호화
    CK = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    body = nonce + AESGCM(CK).encrypt(nonce, gz, None)   # nonce 를 앞에 붙여 한 덩어리로

    # 2) 암호마다 CK 를 감싼다 (salt 를 공유해 해제 시 PBKDF2 는 딱 1회)
    salt = secrets.token_bytes(16)
    MASTER = base64.b64decode(cfg["secret"])             # 도구 공용 - 새로 만들지 않는다

    def derive(p):
        return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                          salt=salt, iterations=ITER).derive(p.encode("utf-8"))

    def wrap(p, info):
        iv = secrets.token_bytes(12)
        blob = AESGCM(derive(p)).encrypt(iv, json.dumps(info).encode("utf-8"), None)
        return {"iv": base64.b64encode(iv).decode(),
                "blob": base64.b64encode(blob).decode()}

    ck_b64 = base64.b64encode(CK).decode()
    keys = [wrap(a.pw, {"ck": ck_b64, "exp": None, "role": "teacher", "label": "교사용",
                        "ms": base64.b64encode(MASTER).decode(),
                        "epoch": start.isoformat(), "weeks": nweeks,
                        "prefix": cfg["prefix"]})]

    print("  키 감싸기 교사용 1개 + 학생용 %d주치 ..." % nweeks, end="", flush=True)
    sheet = weekly.weeks(cfg)
    for n, d0, d1, c in sheet:
        keys.append(wrap(c, {"ck": ck_b64, "nbf": d0.isoformat(), "exp": d1.isoformat(),
                             "role": "student", "label": d0.isoformat()}))
    print(" 완료")
    secrets.SystemRandom().shuffle(keys)                 # 어느 것이 교사용인지 감춘다

    # 3) 교재 그림도 같은 내용키(CK)로 잠근다. img/*.jpg -> enc/*.jpg.enc
    #
    #    ⚠️ 캐시 함정 — 다시 빌드하면 CK 가 새로 생기는데, 브라우저가 옛 .enc 를
    #    캐시에서 꺼내 쓰면 복호화가 조용히 실패해 그림이 빈 칸으로만 보인다.
    #    그래서 빌드마다 표식(build)을 bank.enc 에 넣고, 화면은 그림 주소에
    #    ?b=<표식> 을 붙여 받는다.
    build_id = secrets.token_hex(4)
    src_dir = os.path.join(HERE, "img")
    out_dir = os.path.join(HERE, "enc")
    if os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            os.remove(os.path.join(out_dir, f))
    else:
        os.makedirs(out_dir)
    nimg = 0
    if os.path.isdir(src_dir):
        for name in sorted(os.listdir(src_dir)):
            raw_img = io.open(os.path.join(src_dir, name), "rb").read()
            iv = secrets.token_bytes(12)
            io.open(os.path.join(out_dir, name + ".enc"), "wb").write(
                iv + AESGCM(CK).encrypt(iv, raw_img, None))
            nimg += 1

    io.open(OUT, "w", encoding="utf-8").write(json.dumps({
        "v": 2, "cipher": "AES-GCM", "gz": True, "n": sum(len(g["qs"]) for g in items),
        "build": build_id, "imgs": nimg,
        "nx": sum(len(e["qs"]) for e in exams), "rounds": len(exams),
        "secs": sum(len(c["secs"]) for c in concept),
        "kdf": {"name": "PBKDF2", "hash": "SHA-256", "iter": ITER,
                "salt": base64.b64encode(salt).decode()},
        "data": base64.b64encode(body).decode(),
        "keys": keys,
    }))

    # 화면이 부르는 스크립트 주소에도 표식을 박는다.
    # 안 하면 브라우저가 옛 index.html 스크립트를 캐시에서 꺼내 쓸 수 있다.
    fp = os.path.join(HERE, "index.html")
    if os.path.exists(fp):
        html = io.open(fp, encoding="utf-8").read()
        fixed = re.sub(r'(<body[^>]*data-build=")[^"]*(")', r'\g<1>' + build_id + r'\g<2>', html)
        if fixed != html:
            io.open(fp, "w", encoding="utf-8").write(fixed)

    cur = weekly.this_week(cfg)
    nq = sum(len(g["qs"]) for g in items)
    print("  단원 %d개 · 문항 %d개 · 원본 %dKB -> gzip %dKB -> bank.enc %dKB"
          % (len(items), nq, len(raw) // 1024, len(gz) // 1024, os.path.getsize(OUT) // 1024))
    print("  개념 %d단원 · %d섹션" % (len(concept), sum(len(c["secs"]) for c in concept)))
    print("  기출 %d회차 · %d문항" % (len(exams), sum(len(e["qs"]) for e in exams)))
    print("  교재 그림 %d장 -> enc/*.enc  (빌드 표식 %s)" % (nimg, build_id))
    print("")
    print("  교사용 암호 : %s   (만료 없음)" % a.pw)
    print("  학생 코드   : %d주치  %s ~ %s  (도구 공용)" % (nweeks, start, sheet[-1][2]))
    if cur:
        print("  이번 주 코드: %s %s   (%s ~ %s)" % (cur[3][:4], cur[3][4:], cur[1], cur[2]))


if __name__ == "__main__":
    main()
