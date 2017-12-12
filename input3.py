def banner() :
	print("======================")
	print("--------GuGuDan-------")
	print("======================")

def main() :
	banner()

	for x in range(1,10):
		print("=== %d Dan ==="%(x))
		for y in range(1,10):
			print("%d * %d = %d"%(x, y, x*y))
		print("=============")

if __name__ == "__main__" :
	main()
