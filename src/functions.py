import re
import os
import shutil
from htmlnode import HTMLNode, ParentNode, LeafNode
from textnode import TextNode, TextType
from blocks import BlockType
import textnode


def text_node_to_html_node(text_node: TextNode) -> LeafNode:
	text_node.text = text_node.text.replace("\n"," ")
	match (text_node.text_type):
		case TextType.TEXT:
			return LeafNode(None, text_node.text)
		case TextType.BOLD:
			return LeafNode('b', text_node.text)
		case TextType.ITALIC:
			return LeafNode('i', text_node.text)
		case TextType.CODE:
			return LeafNode('code', text_node.text)
		case TextType.LINK:
			if text_node.url is None:
				raise ValueError("invalid URL")
			return LeafNode('a', text_node.text, {"href": text_node.url})
		case TextType.IMAGE:
			if text_node.url is None:
				raise ValueError("invalid URL")
			return LeafNode('img', '', {"src": text_node.url, "alt": text_node.text})


def split_nodes_delimiter(old_nodes: list[TextNode], delimiter: str, text_type: TextType) -> list[TextNode]:
	new_nodes = []
	for old_node in old_nodes:
		if old_node.text_type != TextType.TEXT:
			new_nodes.append(old_node)
			continue
		split_nodes = []
		sections = old_node.text.split(delimiter)
		if len(sections) % 2 == 0:
			raise ValueError("invalid markdown, formatted section not closed")
		for i in range(len(sections)):
			if sections[i] == "":
				continue
			if i % 2 == 0:
				split_nodes.append(TextNode(sections[i], TextType.TEXT))
			else:
				split_nodes.append(TextNode(sections[i], text_type))
		new_nodes.extend(split_nodes)
	return new_nodes

def extract_markdown_images(text: str):
	return re.findall(r"\!\[([^\[\]]*)\]\(([^\(\)]*)\)",text)

def extract_markdown_links(text: str):
	return re.findall(r"(?<!\!)\[([^\[\]]*)\]\(([^\(\)]*)\)",text)

def split_nodes_image(old_nodes: list[TextNode]) -> list[TextNode]:
	new_nodes = []
	for node in old_nodes:
		if node.text_type != TextType.TEXT:
			new_nodes.append(node)
			continue
		text = node.text
		images = extract_markdown_images(text)
		if len(images) == 0:
			new_nodes.append(node)
			continue

		for image in images:
			needle = f"![{image[0]}]({image[1]})"
			i = text.find(needle)
			s = text[:i]
			if s != "":
				new_nodes.append(TextNode(s,TextType.TEXT))
			new_nodes.append(TextNode(image[0],TextType.IMAGE, image[1]))
			text = text[i+len(needle):]
		if text != "":
			new_nodes.append(TextNode(text,TextType.TEXT))
	return new_nodes
		



def split_nodes_link(old_nodes: list[TextNode]) -> list[TextNode]:
	new_nodes = []
	for node in old_nodes:
		if node.text_type != TextType.TEXT:
			new_nodes.append(node)
			continue
		text = node.text
		links = extract_markdown_links(text)
		if len(links) == 0:
			new_nodes.append(node)
			continue

		for link in links:
			needle = f"[{link[0]}]({link[1]})"
			i = text.find(needle)
			s = text[:i]
			if s != "":
				new_nodes.append(TextNode(s,TextType.TEXT))
			new_nodes.append(TextNode(link[0],TextType.LINK, link[1]))
			text = text[i+len(needle):]
		if text != "":
			new_nodes.append(TextNode(text,TextType.TEXT))
	return new_nodes


def text_to_textnodes(text) -> list[TextNode]:
	nodes = split_nodes_image([TextNode(text,TextType.TEXT)])

	nodes = split_nodes_link(nodes)

	nodes = split_nodes_delimiter(nodes,'**',TextType.BOLD)
	nodes = split_nodes_delimiter(nodes,'_',TextType.ITALIC)
	nodes = split_nodes_delimiter(nodes,'`',TextType.CODE)
	return nodes

def markdown_to_blocks(markdown: str) -> list[str]:
	lines = []
	for line in markdown.split("\n\n"):
		tmp = line.strip()
		if tmp == "":
			continue
		if tmp.endswith("\n"):
			tmp = tmp[0:-2]
		lines.append(tmp)
	return lines

def block_to_block_type(block: str) -> BlockType:
	if re.match(r"#{1,6} .*",block, re.DOTALL):
		return BlockType.HEADING
	elif re.match(r"```\n.*```",block, re.DOTALL):
		return BlockType.CODE

	lines = block.split("\n")

	quote = True
	for line in lines:
		if not re.match(r"> ?",line):
			quote = False
			break
	if quote:
		return BlockType.QUOTE
	
	unordered_list = True
	for line in lines:
		if not re.match(r"- ",line):
			unordered_list = False
			break
	if unordered_list:
		return BlockType.UNORDERED_LIST

	ordered_list = True
	for i in range(len(lines)):
		if not lines[i].lstrip().startswith(f"{i+1}. "):
			ordered_list = False
			break
	if ordered_list:
		return BlockType.ORDERED_LIST
	
	return BlockType.PARAGRAPH

def text_to_children(text: str,block_type : BlockType) -> list[HTMLNode]:
	children_text_node = text_to_textnodes(text)
	children_html_node =[]
	for text_node in children_text_node:
		children_html_node.append(text_node_to_html_node(text_node))
	return children_html_node



def markdown_to_html_node(markdown: str) -> HTMLNode:
	block_to_tag_dict = {
		BlockType.PARAGRAPH : "p",
    	BlockType.HEADING : "h",
    	BlockType.CODE : "pre",
    	BlockType.QUOTE : "blockquote",
    	BlockType.UNORDERED_LIST : "ul",
    	BlockType.ORDERED_LIST : "ol"
    }

	blocks = markdown_to_blocks(markdown)
	pchild = []
	for block in blocks:
		block = block.strip()
		block_type = block_to_block_type(block)
		if block_type == BlockType.HEADING:
			n = 0 
			for i in block.lstrip():
				if i != "#":
					break
				n+=1
			tag = f"h{n}"
			block = block[n+1:]
		elif block_type == BlockType.PARAGRAPH:
			tag = "p"
		elif block_type == BlockType.QUOTE:
			tmp = ""
			for line in block.split("\n"):
				tmp+= line[1:] + " "
			block = tmp.strip()
			tag = "blockquote"
		elif block_type == BlockType.UNORDERED_LIST:
			tmp = ""
			for line in block.split("\n"):
				tmp+= f"<li>{line[2:]}</li>"
			block = tmp
			tag = "ul"
		elif block_type == BlockType.ORDERED_LIST:
			tmp = ""
			for line in block.split("\n"):
				tmp+= f"<li>{line[3:]}</li>"
			block = tmp
			tag = "ol"
		elif block_type == BlockType.CODE:
			block = block.replace("```\n","").replace("```","")
			tag = "pre"


		if block_type == BlockType.CODE:
			children = [LeafNode("code",block)]
		else:
			children = text_to_children(block,block_type)

		
		blockNode = ParentNode(tag,children)
		pchild.append(blockNode)

	return ParentNode('div',pchild)


def extract_title(markdown: str) -> str:
	blocks = markdown_to_blocks(markdown)
	if not blocks[0].lstrip().startswith("# "):
		raise Exception("Hader not found")

	return blocks[0].strip()[2:]


def generate_page(from_path, template_path, dest_path, basepath):
	print(f"Generating page from {from_path} to {dest_path} using {template_path}")
	file = open(from_path, "r")
	file_temp = open(template_path, "r")

	content = file.read()
	template = file_temp.read()

	content_html = markdown_to_html_node(content).to_html()
	title = extract_title(content)


	page = template.replace('{{ Title }}',title).replace("{{ Content }}",content_html)
	page = page.replace('href="/','href="'+basepath)
	page = page.replace('src="/','src="'+basepath)
	parent = os.path.dirname(dest_path)
	if parent:
		os.makedirs(parent,exist_ok=True)
	with open(dest_path[:-2]+"html","w") as f:
		f.write(page)
	
	file.close()
	file_temp.close()








