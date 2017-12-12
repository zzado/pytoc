from pwn import *
import sys, os
from colorama import init
init(strip=not sys.stdout.isatty())
from termcolor import cprint 
from pyfiglet import figlet_format

"""
	2017 Compiler Project PytoC

"""

func_dict = {"len":"strlen","else":"else","raw_input":"scanf", "if":"if", "print":"printf", "while":"while", "for":"for", "return":"return"}

class TOKEN :
	def __init__(self, code):
		self.code = code
		self.depth = 0
		self.opcode = ""
		self.operand = ""	
		self.type = 0 # type 1 is var # 2 is def
		self.flag = 0
		self.result = ""
	
	def _deter_type(self) :
		if self.depth == 0 and ("def" in self.code):
			self.type = 2 # def
			self.code = self.code.replace(":","")
			self.code = self.code.replace("def", "")
			self.code = self.code.replace(" ", "")
		elif self.code.count("=") is 1 and ("print" not in self.code):  # var
			if not "raw_input" in self.code :
				self.type = 1
		

	def parse(self):
		self.depth = self.code.count("\t")
		self.code = self.code.strip("\t")
		self.code = self.code.strip("\n")
		
		if self.code == "": 
			return 0

		self._deter_type()	

		if self.type == 2 :
			self.code = self.code.replace(":","")
			self.opcode = self.code.split("(")[0]
			self.operand = self.code.split("(")[1].strip(")")
			return 1

		if self.type == 1 :
			self.opcode  = self.code.split("=")[0]
			self.operand = self.code.split("=")[1]
			return 1

		if self.type == 0:
			for f in func_dict : 
				if f in self.code :
					self.opcode = func_dict[f]
					self.operand = self.code.strip("\n")
					self.operand = self.operand.replace("len", "strlen")
					if f == "raw_input" :
						self.operand = self.operand.split(f)[0]
					else :
						self.operand = self.operand.split(f)[1]
					return 1
			self.opcode = self.code
			self.operand = ""
			return 1

		return 0
	
	def _info(self):
		log.info("======= Token Info =======")
		log.info("Depth : %d | Type : %d | Opcode : %s | Operand %s"%(self.depth, self.type, self.opcode, self.operand))
		log.info("==========================")


class VAR :
	def __init__(self, token) : 
		self.name = token.opcode
		self.value = token.operand.replace(" ", "")
		self.type = self._deter_type()	

	def _deter_type(self) :
		if '"' in self.value :
			return "char*"
		else :
			return "int"

class FUNC : 
	def __init__(self, token) :
		self.name = token.opcode 
		self.args = token.operand
		self.type = "void" #default void
		self.argv = list()
		self.code = list()
		self.var_list = list()
		self.logic_list = list()
		self._deter_argv()

	def _deter_argv(self):
		self.args = self.args.strip(" ")
		self.argv = list(self.args.split(","))

	
class PYTOC:
	def __init__(self, token_list) :
		self.token_list = token_list
		self.func_list = list()
		pr = log.progress("PyToC")
		try:
			self._pass0()
			pr.status("Progress - Pass0...")
			sleep(0.5)
			self._pass1()
			pr.status("Progress - Pass1...")
			sleep(0.5)
			self._pass2()
			pr.status("Progress - Pass2...")
			sleep(0.5)
			pr.success("Convert python code to C code successfully!")
		except:
			pr.failure("Error - pass1 failed")
			exit()
		
		#self._generate_code()
	
	def _pass0(self) :
		for tk in self.token_list :
			if tk.type == 2 : 
				f = FUNC(tk)
				self.func_list.append(f)
			else :
				f.code.append(tk)

	def _pass1(self):
		for func in self.func_list :
			for tk in func.code :
				if tk.type == 1 : 
					v = VAR(tk)
					func.var_list.append( v )
				else :
					func.logic_list.append( tk )

	def _pass2(self) :
		for func in self.func_list :
			for tk in func.logic_list :
				self._handler(func, tk)
	
	def _handler(self, func, tk):
		if tk.opcode is "else":
			tk.result = "%s"%(tk.opcode)
			tk.flag = 1
			return
		if tk.opcode is "if":
			tk.operand = tk.operand.replace(":","")			
			tk.result = "%s%s"%(tk.opcode, tk.operand)
			tk.flag = 1
			return
		if tk.opcode is "for":
			tk.operand = tk.operand.replace(":","")		
			var1 = tk.operand.split("in")[0].replace(" ","")
			var2 = tk.operand.split("range")[1].replace("(","").replace(")","")
			var3 = var2.split(",")[0]
			var4 = var2.split(",")[1]
			tk.operand = "int %s=%s;%s<%s;%s++"%(var1,var3,var1,var4,var1)
			tk.result = "%s(%s)"%(tk.opcode, tk.operand)
			tk.flag = 1 
			return
		if tk.opcode is "while":
			return
		if tk.opcode is "printf":
			if "%" in tk.operand : # format string 
				
				fs = tk.operand.rfind("%")
				tk.operand = tk.operand[:fs] + "," + tk.operand[fs+1:].replace("(","").replace(")","") + ")"
			tk.result = "%s%s;puts(\"\");"%(tk.opcode, tk.operand)
			return 

		if tk.opcode is "scanf":
			tk.operand = tk.operand.replace(" ", "")
			tk.operand = tk.operand.replace("=", "")
			func.var_list.append("char %s[100];"%(tk.operand))
			tk.operand = "\"%s\",&" + tk.operand
			tk.result = "%s(%s);"%(tk.opcode, tk.operand)
			return

		if tk.operand is not "" :	
			tk.result = "%s(%s);"%(tk.opcode, tk.operand)
			return
		else :
			tk.result = "%s;"%(tk.opcode)
			return

	def _generate_code(self) :
		for func_idx, func in enumerate(self.func_list) :
			print "%s %s(%s){"%(func.type, func.name, func.argv)
			indent = 1	
			for var in func.var_list :
				if not type(var) is str:
					print "\t%s %s=%s;"%(var.type, var.name, var.value)
				else :
					print "\t%s"%(var)

			for idx, tk in enumerate(func.logic_list): 
				if indent > tk.depth:
					print "\t"*(indent-1) + "}"# %d %d"%(tk.depth, indent)
					indent = indent-1
				if indent < tk.depth:
					print "\t"*indent + "{"# %d %d"%(tk.depth, indent)	
					indent = indent+1	
			
				if (tk.type is 0) and (tk.result is not ""):
					print "\t"*tk.depth + tk.result
		
			for x in range(indent, 0, -1):
				print "\t"*(x-1) + "}"	

	def save(self, output) :
		p = log.progress("PyToC")
		try :
			os.system("mkdir ./"+output)
			f = open("./"+output+"/"+output+".c", "w")
			m = open("./"+output+"/Makefile", "w")
			p.status("File open success")
		except :
			p.failure("Error - File open failed!")
			exit()

		f.write("#include<stdio.h>\n#include<stdlib.h>\n\n")
		for func_idx, func in enumerate(self.func_list) :
			f.write("%s %s(%s){\n"%(func.type, func.name, func.args))
			indent = 1	
			for var in func.var_list :
				if not type(var) is str:
					f.write("\t%s %s=%s;\n"%(var.type, var.name, var.value))
				else :
					f.write("\t%s\n"%(var))

			for idx, tk in enumerate(func.logic_list): 
				if indent > tk.depth:
					f.write("\t"*(indent-1) + "}\n")
					indent = indent-1
				if indent < tk.depth:
					f.write("\t"*indent + "{\n")	
					indent = indent+1	
			
				if (tk.type is 0) and (tk.result is not ""):
					f.write("\t"*tk.depth + tk.result + "\n")
		
			for x in range(indent, 0, -1):
				f.write("\t"*(x-1) + "}\n")
		sleep(1)
		f.close()
		
		m.write("CC = gcc\n")
		m.write("%s : %s.c\n"%(output, output))
		m.write("\tgcc -o %s %s.c"%(output, output))
		m.close()
		p.success("Create C source code & Makefile in %s directory!"%(output))

class Tokenizer:
	def __init__(self) :
		self.file_path = ""
		self.token_list = list()		
		self._start()

	def _banner(self):
		cprint(figlet_format("PyToC", font="larry3d"),'green', attrs=['bold'])

	def _start(self):
		self.file_path = raw_input("[*] Input python source code to convert >> ")
		self.file_path = self.file_path.strip("\n")
		self.file_path = self.file_path.split(".")[0]
		p = log.progress("Tokenizer")
		try :
			self.fd = open(self.file_path+".py", "r")
			p.status("File open success")
		except :
			p.failure("Error - File open failed!")
			exit()
		while( True ) :
			line = self.fd.readline()
			if "__name__" in line : break;
			if not line : break;
			token = TOKEN(line)
			if( token.parse() ) :
				self.token_list.append(token)
		self.fd.close()
		sleep(1)
		p.success("Tokenize Done!")

def banner():
	cprint(figlet_format("PyToC", font="larry3d"),'green', attrs=['bold'])

def main():
	banner()
	tkizer = Tokenizer()
	_pytoc = PYTOC(tkizer.token_list)
	_pytoc.save(tkizer.file_path)

if __name__ == "__main__" :
	main()
