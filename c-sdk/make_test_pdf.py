"""Generate a tiny valid PDF used as the embedded /pdf/test.pdf served by the C version.

Run this once, then `xxd -i test.pdf > pdf_data.h` to regenerate the embedded
byte array if you want to change the contents.
"""

objs = []
objs.append(b"<</Type/Catalog/Pages 2 0 R>>")
objs.append(b"<</Type/Pages/Kids[3 0 R]/Count 1>>")
objs.append(
    b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 120]"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>"
)
stream = b"BT /F1 18 Tf 20 60 Td (Hello from Pico W) Tj ET"
objs.append(b"<</Length " + str(len(stream)).encode() + b">>stream\n" + stream + b"\nendstream")
objs.append(b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")

pdf = b"%PDF-1.4\n"
offsets = [0]
for i, obj in enumerate(objs, start=1):
    offsets.append(len(pdf))
    pdf += f"{i} 0 obj ".encode() + obj + b" endobj\n"

xref_off = len(pdf)
pdf += b"xref\n0 " + str(len(objs) + 1).encode() + b"\n"
pdf += b"0000000000 65535 f \n"
for off in offsets[1:]:
    pdf += f"{off:010d} 00000 n \n".encode()
pdf += (
    b"trailer <</Size " + str(len(objs) + 1).encode() + b"/Root 1 0 R>>\n"
    b"startxref\n" + str(xref_off).encode() + b"\n%%EOF\n"
)

with open("test.pdf", "wb") as f:
    f.write(pdf)
print(f"wrote test.pdf ({len(pdf)} bytes)")
