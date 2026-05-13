import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'templates\dashboard\home.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(12, 32):
    sys.stdout.write(f"LINE {i+1}: {repr(lines[i])}\n")
