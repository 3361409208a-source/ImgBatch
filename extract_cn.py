import re

PATH = r"C:\Users\Administrator\Desktop\球员\ImgBatch\image_compressor.pyw"

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Extract Chinese strings from text=, title=, heading(..., text=)
results = []

# text='...' or text="..."
for pattern in [
    r"text='([^']*[一-鿿][^']*)'",
    r'text="([^"]*[一-鿿][^"]*)"',
    r"title='([^']*[一-鿿][^']*)'",
    r'title="([^"]*[一-鿿][^"]*)"',
]:
    results.extend(re.findall(pattern, content))

# heading('col', text='...')
results.extend(re.findall(r"heading\([^)]+text='([^']*[一-鿿][^']*)'", content))
results.extend(re.findall(r'heading\([^)]+text="([^"]*[一-鿿][^"]*)"', content))

# messagebox.showinfo('title', 'msg')
results.extend(re.findall(r"messagebox\.\w+\('([^']*[一-鿿][^']*)'", content))
results.extend(re.findall(r'messagebox\.\w+\("([^"]*[一-鿿][^"]*)"', content))

# filedialog title
results.extend(re.findall(r"title='([^']*[一-鿿][^']*)'", content))

# unique and sort
unique = sorted(set(results))
print(f"Found {len(unique)} unique Chinese UI strings:")
print("=" * 60)
for s in unique:
    print(repr(s))
