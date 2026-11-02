from textnode import TextNode


def main():
	obj = TextNode("This is some anchor text", "link", "https://www.boot.dev")
	print(obj)

if __name__ == '__main__':
	main()