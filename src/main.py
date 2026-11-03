import shutil
import os
import sys
from pathlib import Path
from functions import generate_page


def main():
	basepath = "/"
	if len(sys.argv) > 1:
		basepath = sys.argv[1]

	update_content(basepath)

def update_content(basepath):
	src_dir = Path(__file__).resolve().parent
	parent = src_dir.parent
	parent_dir = str(parent)
	static_path = os.path.join(parent,"static/")
	public_path = os.path.join(parent,"docs/")
	content_path = os.path.join(parent,"content/")
	print (parent_dir)
	shutil.rmtree(public_path,ignore_errors=True)
	os.mkdir(public_path)

	copy_dir(static_path,public_path)

	generate_all(content_path,parent_dir+"/template.html",public_path,basepath)	


def generate_all(content_path,template_path,public_path,basepath):
	for f in os.listdir(content_path):
		if os.path.isfile(content_path+f):
			generate_page(content_path+f,template_path,public_path+f,basepath)
		else:
			generate_all(content_path+f+"/",template_path,public_path+f+"/",basepath)

def copy_dir(a: str, b: str):
	for f in os.listdir(a):
		if os.path.isfile(a+f):
			shutil.copy(a+f,b)
		else:
			if not os.path.exists(b+f):
				os.mkdir(b+f)
			copy_dir(a+f+"/",b+f+"/")


if __name__ == '__main__':
	main()