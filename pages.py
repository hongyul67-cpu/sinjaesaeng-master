# 스캔 PDF 쪽을 PNG 로 뽑아 **모든 세션이 함께 쓰는 폴더**에 둔다.
#
#   python pages.py <A|B|C> [시작쪽인덱스] [끝쪽인덱스]      끝은 포함
#   python pages.py B 61 78
#   python pages.py C            (전부)
#
# 왜 공용 폴더인가: 세션마다 scratchpad 가 달라서, 각자 렌더하면 같은 일을
# 여러 번 하게 된다. 저장소 밖(_scan_신재생)에 두어 커밋되지 않게 한다.
import os, sys, fitz

D = r"C:/Users/user/Desktop/업무폴더/01_수업/2025이전_수업/신재생에너지"
PDF = {
    "A": "2026-06-29 09_59_14.pdf",   # 적중예상문제  p.115~346
    "B": "2026-06-29 11_04_23.pdf",   # 기출 2016-2 ~ 2019-3
    "C": "2026-06-29 11_58_15.pdf",   # 기출 2020-2 ~ 2025-4
}
OUT = r"C:/Users/user/Desktop/claude code/_scan_신재생"


def main():
    key = sys.argv[1].upper()
    doc = fitz.open(os.path.join(D, PDF[key]))
    a = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    b = int(sys.argv[3]) if len(sys.argv) > 3 else len(doc) - 1
    out = os.path.join(OUT, "p" + key)
    os.makedirs(out, exist_ok=True)

    made = skipped = 0
    for i in range(a, min(b, len(doc) - 1) + 1):
        f = os.path.join(out, "%03d.png" % i)
        if os.path.exists(f):
            skipped += 1
            continue
        doc[i].get_pixmap(dpi=80).save(f)
        made += 1
    doc.close()
    print("%s %d~%d 쪽 → %s  (새로 %d장, 이미 있던 것 %d장)"
          % (key, a, b, out, made, skipped))


if __name__ == "__main__":
    main()
