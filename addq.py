# 전사한 문항 조각을 회차 파일(exam/<연도>-<회차>.js) 안에 이어 붙인다.
#
#   python addq.py <연도>-<회차> <붙일조각.js>
#   python addq.py 2018-2 조각.js
#
# 회차 파일이 없으면 만들어 준다(= 그 회차를 찜한다).
#   python addq.py 2018-2 --new "2018년 제2회 과년도 기출복원문제"
#
# 조각 파일에는 문항 객체만 쉼표로 이어 적는다. 배열 괄호는 쓰지 않는다.
#   { no:1, q:"...", ch:["","","",""], a:2, ex:"..." },
#   { no:2, ... },
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "exam")

HEAD = """/* 신재생에너지발전설비기능사(태양광) 필기 — %s
   ⚠️ 평문 원본. .gitignore 에 있으니 절대 커밋하지 말 것.

   회차마다 60문항이 아니다. 교재 426쪽에 이렇게 적혀 있다 —
   "KEC(한국전기설비규정) 적용 및 관련 법령 개정으로 삭제된 문제가 있어
    60문항이 되지 않음을 알려드립니다."
   빠진 번호는 스캔 누락이 아니라 교재가 뺀 것이다. 번호는 원본 그대로 둔다.  */
module.exports =
{ year:%s, round:%s, title:"%s", qs:[

]};
"""
END = "\n]};"


def main():
    tag = sys.argv[1]
    year, rnd = tag.split("-")
    path = os.path.join(DIR, tag + ".js")
    os.makedirs(DIR, exist_ok=True)

    if sys.argv[2] == "--new":
        if os.path.exists(path):
            raise SystemExit("이미 있습니다(다른 세션이 찜했을 수 있음): exam/%s.js" % tag)
        io.open(path, "w", encoding="utf-8").write(HEAD % (sys.argv[3], year, rnd, sys.argv[3]))
        print("찜했습니다: exam/%s.js" % tag)
        return

    if not os.path.exists(path):
        raise SystemExit("exam/%s.js 가 없습니다. 먼저 --new 로 만드세요." % tag)

    piece = io.open(sys.argv[2], encoding="utf-8").read().strip() + "\n"
    s = io.open(path, encoding="utf-8").read()
    i = s.rfind(END)
    if i < 0:
        raise SystemExit("exam/%s.js 에서 qs 배열이 닫히는 자리를 찾지 못했습니다." % tag)
    io.open(path, "w", encoding="utf-8").write(s[:i] + "\n" + piece + s[i:])

    e = None
    try:
        import subprocess, json
        drv = "process.stdout.write(String(require('./exam/%s.js').qs.length))" % tag
        e = subprocess.run(["node", "-e", drv], capture_output=True, text=True, cwd=HERE).stdout
    except Exception:
        pass
    print("붙였습니다: exam/%s.js  (지금 %s문항)" % (tag, e or "?"))


if __name__ == "__main__":
    main()
