import os

def replace_line(file_name, line_num, col_s, col_e, text):
    lines = open(file_name, 'r').readlines()
    temp=lines[line_num]
    temp = temp.replace(temp[col_s:col_e],text)
    lines[line_num]=temp
    out = open(file_name, 'w')
    out.writelines(lines)
    out.close()

for filename in os.listdir(os.getcwd()):
  if filename.endswith(".asc"):
    replace_line(os.path.join(os.getcwd(), filename), 2, 13, 22,"-405000\n")
    replace_line(os.path.join(os.getcwd(), filename), 3, 13, 22,"-625000\n")
