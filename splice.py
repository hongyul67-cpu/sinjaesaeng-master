# concept_book.js 에 단원 블록을 이어 붙인다.
#
#   python splice.py <붙일조각.js> [대상파일]   (대상 기본값 concept_book.js)
#
# 왜 스크립트로 두나: 개념 본문에 백틱·중괄호·따옴표가 잔뜩 들어 있어
# 셸 heredoc 으로 밀어 넣으면 셸이 먼저 삼켜 버린다. 파일로 주고받는다.
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DST = None                                  # main() 에서 정한다
MARK = "\n];\n\nif (typeof window"          # 배열이 닫히는 자리

def main():
    global DST
    DST = os.path.join(HERE, sys.argv[2] if len(sys.argv) > 2 else "concept_book.js")
    piece = io.open(sys.argv[1], encoding="utf-8").read().rstrip() + "\n"
    s = io.open(DST, encoding="utf-8").read()
    if MARK not in s:
        raise SystemExit(os.path.basename(DST) + " 에서 배열이 닫히는 자리를 찾지 못했습니다.")
    s = s.replace(MARK, "\n" + piece + MARK, 1)
    io.open(DST, "w", encoding="utf-8").write(s)
    print("붙였습니다:", os.path.basename(sys.argv[1]), len(piece), "바이트")

if __name__ == "__main__":
    main()
