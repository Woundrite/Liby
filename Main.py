import os
import glfw
import OpenGL.GL as GL
import imgui
from imgui.integrations.glfw import GlfwRenderer
import mysql.connector as sql
import time
from datetime import date, timedelta

class ToastController():
	def __init__(self, width, height, window, font=None, xfont=None):
		self.Toasts = {}
		self.i = 0
		self.width = width
		self.height = height
		self.window = window
		self.font = font
		self.xfont = xfont
		self.pad = [10, 10]
	
	def AddToast(self, Text, timeout=10):
		self.Toasts[str(self.i)] = (Toast(self.i, self.width, self.height, self.window, Text, self.font, self.xfont, timeout))
		self.i+=1

	def Display(self):
		t = []
		for i in self.Toasts:
			if self.Toasts[i].i <= 0:
				t.append(i)

		for i in t:
			del self.Toasts[i]

		j=0
		for i in self.Toasts.values():
			pos = [glfw.get_window_size(self.window)[0]-self.width-self.pad[0], glfw.get_window_size(self.window)[1]-(self.height+self.pad[1])*(j+1)]
			i.Display(pos)
			j+=1
		

class Toast:
	def __init__(self, ToastNumber, width, height, window, Text="", font=None, xfont=None, timeout=10):
		self.Toasts = {}
		self.width = width
		self.height = height
		self.font = font
		self.Text = [str(Text)[0:18]+"..." if len(Text) > 18 else str(Text)][0]
		self.timeout = timeout
		self.ToastName = str(ToastNumber)
		self.window = window
		self.xfont = xfont
		self.ShouldDel = False
		self.time = time.time()
		self.i = 1
	
	def AddButton(self, Text, callback, callbackargs=None, inline=False, font=None, fontcolor=None, bgcolor=None, width=None, height=None):
		if font != None:
			imgui.push_font(font)

		if bgcolor != None:
			imgui.push_style_color(imgui.COLOR_BUTTON, *bgcolor)

		if fontcolor != None:
			imgui.push_style_color(imgui.COLOR_TEXT, *fontcolor)

		width = width if width != None else 100
		height = height if height != None else 20

		if inline == True:
			imgui.same_line()

		if imgui.button(Text, width, height):
			if callbackargs != None:
				callback(callbackargs)
			else:
				callback()

		if fontcolor != None:
			imgui.pop_style_color(1)

		if bgcolor != None:
			imgui.pop_style_color(1)

		if font != None:
			imgui.pop_font()
	
	def CloseToast(self):
		self.i = -1
		self.ShouldDel = True

	def Display(self, pos):
		if self.font != None:
			imgui.push_font(self.font)
		
		if time.time()-self.time >= (self.timeout)/1000:
			self.i -= 0.001
			self.time = time.time()
		
		if self.i >= 0:
			imgui.set_next_window_size(self.width, self.height)
			imgui.set_next_window_position(pos[0], pos[1])
			imgui.begin(self.ToastName, flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_SCROLLBAR)
			imgui.text(self.Text)
			self.AddButton("X", lambda: self.CloseToast(), inline=True, font=self.font, fontcolor=(1.0, 1.0, 1.0, 1.0), bgcolor=(0.0, 0.0, 0.0, 0), width=2*imgui.calc_text_size("X").x, height=1.5*imgui.calc_text_size("X").y)
			imgui.progress_bar(self.i, (self.width, self.height/10))
			imgui.end()
		else:
			self.CloseToast()
		
		if self.font != None:
			imgui.pop_font()

class Graphics:
	def __init__(self, SQL, window, Fonts={}):
		self.Fonts=Fonts
		self.SubSideWindows = [self.SearchBook, self.ReturnBook, self.UpdateRecord, self.RemoveBook ,self.AddBook, self.IssueBook]
		self.SQL = SQL
		self.window = window
		self.AddBookName="Book Name"
		self.AddBookAuthor="Author"
		self.IssueBookNm = ""
		self.SearchBookNm = ""
		self.RemoveBookNm = ""
		self.ReturnBookNm = ""
		self.UpdateRecordNm = ""
		self.IssueBookPersonName = ""
		self.UpdateBookReturnDate = None
		self.UpdatingList = False
		self.NumBookAdd = 1
		self.ToastController = ToastController(200, 35, window, font=self.Fonts["FontText"], xfont=self.Fonts["FontSubtitle"])

	def AddButton(self, Text, callback, callbackargs=None, inline=False, font=None, fontcolor=None, bgcolor=None, width=None, height=None):
		if font != None:
			imgui.push_font(font)

		if bgcolor != None:
			imgui.push_style_color(imgui.COLOR_BUTTON, *bgcolor)

		if fontcolor != None:
			imgui.push_style_color(imgui.COLOR_TEXT, *fontcolor)
		
		width = width if width != None else 150
		height = height if height != None else 20

		if inline==True:
			imgui.same_line()
		
		if imgui.button(Text, width, height):
			if callbackargs != None:
				callback(callbackargs)
			else:
				callback()
		
		if fontcolor != None:
			imgui.pop_style_color(1)

		if bgcolor != None:
			imgui.pop_style_color(1)
		
		if font != None:
			imgui.pop_font()

	def NullCallback(self):
		print("Foo") #USEFUL FOR TEMP TODOS
	
	def ConfirmBookAdd(self,NoClose=False):
		if not NoClose:
			self.SubSideWindows.remove(self.AddBook)
		self.SQL.AddBook(self.AddBookName, self.AddBookAuthor)
		self.ToastController.AddToast("Added Book: "+ self.AddBookName, 10)
		self.AddBookName = "Book Name"
		self.AddBookAuthor = "Author"
		self.ToastController.AddToast("Added Book: "+self.AddBookName, 10)

	def AddBook(self):
		imgui.set_next_window_size(400, 120)
		imgui.set_next_window_position(420, 10)
		imgui.begin( "Add Book", flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE )
		changed, text_val_book_name = imgui.input_text(': Book Name', self.AddBookName, 256)
		changed, text_val_book_author = imgui.input_text(': Book Author', self.AddBookAuthor, 256)
		self.AddBookName = text_val_book_name if text_val_book_name not in ["Book Name", ""] else self.AddBookName
		self.AddBookAuthor = text_val_book_author if text_val_book_author not in ["Book Author", ""] else self.AddBookAuthor
		self.AddButton("Add Another Book", lambda: self.ConfirmBookAdd(NoClose=True), inline=False, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1), width=180)
		self.AddButton("Add Book", lambda: self.ConfirmBookAdd(), inline=True, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1))
		imgui.end()
	
	def RemoveBookFromList(self, elem):
		self.SQL.RemoveBook(elem[0])
		self.ToastController.AddToast("Removed Book: "+ self.AddBookName, 10)

	def RemoveBook(self):
		BookList = self.SQL.GetBooks()
		imgui.set_next_window_size(400, 350)
		imgui.set_next_window_position(830, 10)
		imgui.begin("Remove Book", flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE)
		changed, text_val_book_search = imgui.input_text(': Book Search', self.RemoveBookNm, 256)
		self.RemoveBookNm = text_val_book_search #if text_val_book_search not in [""] else self.RemoveBookNm
		imgui.separator()
		for i in BookList:
			if ((self.RemoveBookNm in i[1]) or (self.RemoveBookNm in i[2]) or (self.RemoveBookNm == "")):
				imgui.text(f"{i[0]}: {i[1]}")
				imgui.push_font(self.Fonts["FontSubtitle"])
				self.AddButton(f"Remove##{i[0]}", lambda: self.RemoveBookFromList(i), inline=True, fontcolor=(1.0, 1.0, 1.0, 1.0), bgcolor=(0.0, 0.0, 0.0, 0), width=2*imgui.calc_text_size("Remove").x, height=1.5*imgui.calc_text_size("Remove").y)
				imgui.text(f"by - {i[2]}")
				imgui.pop_font()
				imgui.separator()
		imgui.end()

	def SearchBook(self):
		BookList = self.SQL.GetBooks()
		imgui.set_next_window_size(400, 350)
		imgui.set_next_window_position(10, 140)
		imgui.begin("Search Book", flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE)
		changed, text_val_book_search = imgui.input_text(': Book Search', self.SearchBookNm, 256)
		self.SearchBookNm = text_val_book_search #if text_val_book_search not in [""] else self.SearchBookNm
		imgui.separator()
		for i in BookList:
			if ((self.SearchBookNm in i[1]) or (self.SearchBookNm in i[2]) or (self.SearchBookNm == "")):
				imgui.text(f"{i[0]}: {i[1]}")
				imgui.push_font(self.Fonts["FontSubtitle"])
				imgui.text(f"by - {i[2]}")
				imgui.pop_font()
				imgui.separator()
		imgui.end()

	def IssueBookFromList(self, elem=None):
		self.IssueBookNum = elem
		self.SubSideWindows.append(self.__IssueBookFromList)

	def ConfirmIssue(self, close=True):
		self.SQL.IssueBook(self.IssueBookNum[0], self.IssueBookPersonName)
		self.IssueBookPersonName = ""
		if close:
			self.SubSideWindows.remove(self.__IssueBookFromList)
		self.ToastController.AddToast("Issued Book: "+ self.IssueBookNum[1], 10)

	def __IssueBookFromList(self):
		imgui.set_next_window_size(400, 120)
		imgui.set_next_window_position(420, 140)
		imgui.begin("Issue Book##1", flags=imgui.WINDOW_NO_RESIZE |imgui.WINDOW_NO_COLLAPSE)
		changed, text_val_issue_name = imgui.input_text(': Issuer Name', self.IssueBookPersonName, 256)
		self.IssueBookPersonName = text_val_issue_name if text_val_issue_name not in ["Book Name", ""] else self.IssueBookPersonName
		self.AddButton("Issue Book", lambda: self.ConfirmIssue(), inline=False, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1))
		self.AddButton("Issue Another Book", lambda: self.ConfirmIssue(close=False), inline=True, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1))
		imgui.end()
	
	def IssueBook(self):
		BookList = self.SQL.GetBooks()
		imgui.set_next_window_size(400, 350)
		imgui.set_next_window_position(420, 140)
		imgui.begin("Issue Book", flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE)
		changed, text_val_book_issue_search = imgui.input_text(': Book Search', self.IssueBookNm, 256)
		self.IssueBookNm = text_val_book_issue_search# if text_val_book_issue_search not in ["Book Name", ""] else self.IssueBookNm
		imgui.separator()
		for i in BookList:
			if ((self.IssueBookNm in i[1]) or (self.IssueBookNm in i[2]) or (self.IssueBookNm == "")):
					if i[3] == None:
						imgui.text(f"{i[0]}: {i[1]}")
						imgui.push_font(self.Fonts["FontSubtitle"])
						self.AddButton(f"Issue##{i[0]}", lambda: self.IssueBookFromList(i), inline=True, fontcolor=(1.0, 1.0, 1.0, 1.0), bgcolor=(0.0, 0.0, 0.0, 0), width=2*imgui.calc_text_size("Remove").x, height=1.5*imgui.calc_text_size("Remove").y)
						imgui.text(f"by - {i[2]}")
						if i[3] != None:
							imgui.same_line()
							imgui.text(f" - issued by: {i[3]}")
						imgui.pop_font()
						imgui.separator()
		imgui.end()

	def ReturnBookFromList(self, i):
		if date.today() < i[4]:
			self.ToastController.AddToast("Late: Fine 100rs", 10)
		self.SQL.ReturnBook(i[0])
		self.ToastController.AddToast("Book Returned", 10)
	
	def ReturnBook(self):
		BookList = self.SQL.GetBooks()
		imgui.set_next_window_size(400, 340)
		imgui.set_next_window_position(830, 370)
		imgui.begin("Return Book", flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE)
		changed, text_val_book_return_search = imgui.input_text(': Book Search', self.ReturnBookNm, 256)
		self.ReturnBookNm = text_val_book_return_search if text_val_book_return_search not in ["Book Name", ""] else self.ReturnBookNm
		imgui.separator()
		for i in BookList:
			if ((self.ReturnBookNm in i[1]) or (self.ReturnBookNm in i[2]) or (self.ReturnBookNm == "")):
				if i[3] != None:
					imgui.text(f"{i[0]}: {i[1]}")
					imgui.push_font(self.Fonts["FontSubtitle"])
					# self.AddButton(f"Remove##{i[0]}", lambda: self.RemoveBookFromList(i), inline=True, fontcolor=(1.0, 1.0, 1.0, 1.0), bgcolor=(0.0, 0.0, 0.0, 0), width=2*imgui.calc_text_size("Remove").x, height=1.5*imgui.calc_text_size("Remove").y)
					self.AddButton(f"Return##{i[0]}", lambda: self.ReturnBookFromList(i), inline=True, fontcolor=(1.0, 1.0, 1.0, 1.0), bgcolor=(0.0, 0.0, 0.0, 0), width=2*imgui.calc_text_size("Remove").x, height=1.5*imgui.calc_text_size("Remove").y)
					imgui.text(f"by - {i[2]}")
					imgui.same_line()
					imgui.text(f" - issued by: {i[3]}")
					imgui.text(f" - return by: {i[4]}")
					imgui.pop_font()
					imgui.separator()
		imgui.end()

	def UpdateBookFromList(self, i):
		self.UpdateElem = i
		self.UpdatingList = True
		self.UpdateBookName = self.UpdateElem[1]
		self.UpdateBookAuthor = self.UpdateElem[2]
		if self.UpdateElem[3] != None:
			self.UpdateBookIssuer = self.UpdateElem[3]
		else:
			self.UpdateBookIssuer = ""

	def ConfirmBookUpdate(self):
		print(self.UpdateBookIssuer)
		self.SQL.UpdateRecord(self.UpdateElem[0], self.UpdateBookName, self.UpdateBookAuthor, self.UpdateBookIssuer)
		self.UpdateBookName = None
		self.UpdateBookAuthor = None
		self.UpdateBookIssuer = None
		self.UpdateElem = None
		self.UpdatingList = False
		self.ToastController.AddToast("Updated Book: "+self.UpdateBookName, 10)

	def UpdateRecord(self):
		BookList = self.SQL.GetBooks()
		imgui.set_next_window_size(800, 200)
		imgui.set_next_window_position(10, 510)
		UL = self.UpdatingList
		imgui.begin("Update Book Records", flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE)
		if UL:
			imgui.begin_child("List", 400, 200)
		changed, text_val_book_return_search = imgui.input_text(': Book Search', self.UpdateRecordNm, 256)
		self.UpdateRecordNm = text_val_book_return_search if text_val_book_return_search not in ["Book Name", ""] else self.UpdateRecordNm
		imgui.separator()
		for i in BookList:
			if ((self.UpdateRecordNm in i[1]) or (self.UpdateRecordNm in i[2]) or (self.UpdateRecordNm == "")):
				imgui.text(f"{i[0]}: {i[1]}")
				imgui.push_font(self.Fonts["FontSubtitle"])
				self.AddButton(f"Update##{i[0]}", lambda: self.UpdateBookFromList(i), inline=True, fontcolor=(1.0, 1.0, 1.0, 1.0), bgcolor=(0.0, 0.0, 0.0, 0), width=2*imgui.calc_text_size("Remove").x, height=1.5*imgui.calc_text_size("Remove").y)
				imgui.text(f"by - {i[2]}")
				imgui.pop_font()
				imgui.separator()
		if UL:
			imgui.end_child()
			imgui.same_line()

			imgui.begin_child("Update Record", 400, 200)
			changed, text_val_book_name = imgui.input_text(': Book Name', self.UpdateBookName, 256)
			changed, text_val_book_author = imgui.input_text(': Book Author', self.UpdateBookAuthor, 256)
			changed, text_val_book_issuer = imgui.input_text(': Book Issuer', self.UpdateBookIssuer, 256)
			changed, text_val_book_return_date = imgui.input_text(': Issue Date', str(self.UpdateBookReturnDate), 256)
			self.UpdateBookName = text_val_book_name if text_val_book_name not in ["Book Name", ""] else self.UpdateBookName
			self.UpdateBookAuthor = text_val_book_author if text_val_book_author not in ["Book Author", ""] else self.UpdateBookAuthor
			self.UpdateBookIssuer = text_val_book_issuer if text_val_book_issuer not in [""] else self.UpdateBookIssuer
			self.UpdateBookReturnDate = text_val_book_return_date if text_val_book_return_date not in [""] else self.UpdateBookReturnDate
			self.AddButton("Update Record", lambda: self.ConfirmBookUpdate(), inline=False, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1), width=180)
			imgui.end_child()

		imgui.end()

	def step(self):		
		# Set the size of menu and position
		imgui.set_next_window_size(400, 120)
		imgui.set_next_window_position(10,10)
		imgui.push_font(self.Fonts["FontHeader2"])
		#Design the standard Menu
		imgui.begin("Toggle Menu", flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE)
		# print(self.SubSideWindows)
		self.AddButton("Add New Book", lambda: [self.SubSideWindows.append(self.AddBook) if self.AddBook not in self.SubSideWindows else self.SubSideWindows.remove(self.AddBook)], inline=False, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1))
		self.AddButton("Remove Book", lambda: [self.SubSideWindows.append(self.RemoveBook) if self.RemoveBook not in self.SubSideWindows else self.SubSideWindows.remove(self.RemoveBook)], inline=True, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1))
		self.AddButton("Search Book", lambda: [self.SubSideWindows.append(self.SearchBook) if self.SearchBook not in self.SubSideWindows else self.SubSideWindows.remove(self.SearchBook)], inline=False, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1))
		self.AddButton("Issue Book", lambda: [self.SubSideWindows.append(self.IssueBook) if self.IssueBook not in self.SubSideWindows else self.SubSideWindows.remove(self.IssueBook)], inline=True, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1))
		self.AddButton("Return Book", lambda: [self.SubSideWindows.append(self.ReturnBook) if self.ReturnBook not in self.SubSideWindows else self.SubSideWindows.remove(self.ReturnBook)], inline=False, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1))
		self.AddButton("Update Book Records", lambda: self.SubSideWindows.append(self.UpdateRecord) if self.UpdateRecord not in self.SubSideWindows else self.SubSideWindows.remove(self.UpdateRecord), inline=True, font=self.Fonts["FontText"], fontcolor=(0.0, 0.0, 0.0, 1.0), bgcolor=(0.3, 0.9, 0.7, 1))
		imgui.end()
		imgui.pop_font()

		for i in self.SubSideWindows:
			i()
		self.ToastController.Display()


class Backend():
	def __init__(self, usr,passwd,db, tb_nm=""):
		# Connecting to Database
		self.connector = sql.connect(user=usr, password=passwd, host='127.0.0.1')
		self.db = db
		if tb_nm == "":
			tb_nm = db
		self.i = 0
		self.cursor = self.connector.cursor()
		self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db};")
		self.cursor.execute(f"USE {db};")
		self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {tb_nm}(ID int NOT NULL,\
																 BookName varchar(255) NOT NULL,\
																 Author varchar(255) NOT NULL,\
																 Issued varchar(255),\
																 DateOfReturn DATE, \
																 PRIMARY KEY(ID)\
																);")
		self.cursor.execute(f"SELECT ID FROM {db};")

		for i in self.cursor:
			self.i+=1
		
		self.tb_nm = tb_nm
		self.db = db
	
	# def __del__(self):
	# 	self.cursor.execute("commit;")

	def IssueBook(self, ID, Name):
		self.cursor.execute(f"UPDATE {self.tb_nm} SET Issued='{Name}' WHERE ID={ID}")
		self.cursor.execute(f"UPDATE {self.tb_nm} SET DateOFReturn='{str(date.today()+timedelta(days=7))}' WHERE ID={ID}")
		self.connector.commit()

	def ReturnBook(self, ID):
		self.cursor.execute(f"UPDATE {self.tb_nm} SET Issued=NULL WHERE ID={ID}")
		self.connector.commit()

	def AddBook(self, bookName, bookAuthor):
		self.i+=1
		self.cursor.execute(f"INSERT INTO {self.tb_nm} VALUES({str(self.i)}, '{bookName}', '{bookAuthor}', NULL, NULL);")
		self.connector.commit()

	def RemoveBook(self, ID):
		self.i -= 1
		self.cursor.execute(f"DELETE FROM {self.tb_nm} WHERE ID={ID}")

	def GetBooks(self):
		self.cursor.execute(f"SELECT * FROM {self.tb_nm};")
		return [x for x in self.cursor]
	
	def UpdateRecord(self, ID, Nm, Ar, Ir):
		self.cursor.execute(f"UPDATE {self.tb_nm} SET BookName='{Nm}' WHERE ID={ID}")
		self.cursor.execute(f"UPDATE {self.tb_nm} SET Author='{Ar}' WHERE ID={ID}")
		if Ir != "":
			self.cursor.execute(f"UPDATE {self.tb_nm} SET Issued='{Ir}' WHERE ID={ID}")
		else:
			self.cursor.execute(f"UPDATE {self.tb_nm} SET Issued=NULL WHERE ID={ID}")
		self.connector.commit()
		


def main(username="root", password=""):
	# Setup Imgui context/Imgui context Intialisation
	imgui.create_context()

	# Window Variables
	width, height = 1240, 720
	window_name = "Library Management System"

	#initialize glfw
	if not glfw.init():
		print("Could not initialize OpenGL context")
		exit(1)

	# OS X supports only forward-compatible core profiles from 3.2 hence set up glfw window hints
	glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
	glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
	glfw.window_hint(glfw.RESIZABLE, glfw.FALSE) # Make a non resizable window for less headache
	glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
	glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)

	# Create a windowed mode window and its OpenGL context
	window = glfw.create_window(
		int(width), int(height), window_name, None, None
	)
	glfw.make_context_current(window)
	
	#check if window could be formed or not
	if not window:
		glfw.terminate()
		print("Could not initialize Window")
		exit(1)
	
	#setup imgui glfw renderer
	impl = GlfwRenderer(window)

	#get io middleman for higher control
	io = imgui.get_io()

	#initalize fonts
	font_Header1 = io.fonts.add_font_from_file_ttf("Fonts/Monaco.ttf", 25)
	font_Header2 = io.fonts.add_font_from_file_ttf("Fonts/Monaco.ttf", 22)
	font_Header3 = io.fonts.add_font_from_file_ttf("Fonts/Monaco.ttf", 19)
	font_Header4 = io.fonts.add_font_from_file_ttf("Fonts/Monaco.ttf", 16)
	font_Text = io.fonts.add_font_from_file_ttf("Fonts/Monaco.ttf", 13)
	font_Subtitle = io.fonts.add_font_from_file_ttf("Fonts/Monaco.ttf", 10)
	# font_Header4 = io.fonts.add_font_from_file_ttf("Fonts/Monaco.ttf", 30)

	#Recompute textures for the new fonts
	impl.refresh_font_texture()
	GUI = Graphics(SQL=Backend(username,password,"Library"), window = window, Fonts={"FontHeader1":font_Header1, "FontHeader2":font_Header2, "FontHeader3":font_Header3, "FontHeader4":font_Header4, "FontText":font_Text, "FontSubtitle":font_Subtitle})
	#Main Loop
	while not glfw.window_should_close(window):
		#Process events and reset imgui stack for new frame
		glfw.poll_events()
		impl.process_inputs()
		imgui.new_frame()

		#Clear screen
		GL.glClearColor(0.1, 0.1, 0.1, 0.1)
		GL.glClear(GL.GL_COLOR_BUFFER_BIT)
		
		#Main Graphics Function
		GUI.step()

		#Render everyting in stack
		imgui.render()
		impl.render(imgui.get_draw_data())

		#Swap data buffers
		glfw.swap_buffers(window)
	# clear/free renderer and screen to clear memory 
	impl.shutdown()
	glfw.terminate()

if __name__ == "__main__":
	main(password="Codingforlife4ever")
	
	# imgui creates a file called "imgui.ini" that stores position and other data of all other 
	# sub windows to allow continuity of position between runs which we don't want
	try:
		os.remove("imgui.ini")
	except:
		pass