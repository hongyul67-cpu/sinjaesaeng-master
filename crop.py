# 교재 스캔 PDF에서 그림/표를 잘라 img/ 에 저장한다.
#   python crop.py <pdf키> <쪽인덱스> <x0> <y0> <x1> <y1> <파일명.jpg>
# 좌표는 페이지 크기에 대한 비율(0~1). 원본 해상도 그대로 뽑으려면 dpi=110.
import sys, os, fitz

D = r'C:/Users/user/Desktop/업무폴더/01_수업/2025이전_수업/신재생에너지'
PDF = {'A': '2026-06-29 09_59_14.pdf',        # 적중예상문제  p.115~346
       'B': '2026-06-29 11_04_23.pdf',        # 기출 2016-2 ~ 2019-3
       'C': '2026-06-29 11_58_15.pdf'}        # 기출 2020-2 ~ 2025-4
HERE = os.path.dirname(os.path.abspath(__file__))

def crop(key, page, x0, y0, x1, y1, name, dpi=110):
    doc = fitz.open(os.path.join(D, PDF[key]))
    p = doc[page]; r = p.rect
    clip = fitz.Rect(r.x0 + r.width*x0, r.y0 + r.height*y0,
                     r.x0 + r.width*x1, r.y0 + r.height*y1)
    out = os.path.join(HERE, 'img', name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pix = p.get_pixmap(dpi=dpi, clip=clip)
    doc.close()
    # 스캔본이라 PNG 로 두면 잡티까지 무손실로 담겨 한 장에 100KB 를 넘는다.
    # 흑백 사진이므로 회색조 JPEG 로 저장하면 화질 차이 없이 1/10 로 줄어든다.
    from PIL import Image
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples).convert('L')
    im.save(out, quality=82, optimize=True)
    print(name, im.size, os.path.getsize(out)//1024, 'KB')

if __name__ == '__main__':
    a = sys.argv[1:]
    crop(a[0], int(a[1]), *[float(v) for v in a[2:6]], a[6])
