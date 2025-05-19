import tkinter as tk
from tkinter import simpledialog, messagebox
import sqlite3
from datetime import datetime

# Veritabanı bağlantısı
conn = sqlite3.connect("pastane_pos.db")
cursor = conn.cursor()

# Tablo oluşturma
cursor.execute("""
CREATE TABLE IF NOT EXISTS urunler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isim TEXT NOT NULL,
    fiyat REAL NOT NULL,
    kategori TEXT,
    gramaj_bazli INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS satislar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    urun_id INTEGER,
    tarih TEXT,
    gram REAL DEFAULT NULL,
    toplam_fiyat REAL DEFAULT NULL,
    FOREIGN KEY(urun_id) REFERENCES urunler(id)
)
""")
conn.commit()

KATEGORILER = [
    "Tatlı Çeşitleri", "Porsiyonlar", "Sıcak içecekler",
    "Soğuk İçecekler", "Sütlü Tatlılar", "Unlu Mamülleri", "Dondurma"
]

# Renk ayarları
BG_COLOR = "#2c3e50"
FG_COLOR = "#ecf0f1"
CAT_BG = "#34495e"
BTN_BG = "#3498db"
BTN_FG = "#ecf0f1"
FONT = ('Arial', 12)

class POSUygulama:
    def __init__(self, master):
        self.master = master
        master.title("Pastane POS Sistemi")
        master.geometry("1000x700")
        master.configure(bg=BG_COLOR)

        tk.Label(master, text="Ürünler:", font=('Arial', 14, 'bold'), fg=FG_COLOR, bg=BG_COLOR).pack(pady=5)

        # Arama
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.listele_urunler())
        search_entry = tk.Entry(master, textvariable=self.search_var, font=FONT)
        search_entry.pack(pady=5, padx=10, fill="x")
        search_entry.insert(0, "Ürün ara...")

        # Ürün listesi canvas
        canvas_frame = tk.Frame(master, bg=BG_COLOR)
        canvas_frame.pack(fill="both", expand=True)
        self.urunler_canvas = tk.Canvas(canvas_frame, bg=BG_COLOR, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.urunler_canvas.yview)
        self.urunler_frame = tk.Frame(self.urunler_canvas, bg=BG_COLOR)

        self.urunler_frame.bind("<Configure>", lambda e: self.urunler_canvas.configure(scrollregion=self.urunler_canvas.bbox("all")))
        self.urunler_canvas.create_window((0, 0), window=self.urunler_frame, anchor="nw")
        self.urunler_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.urunler_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Sepet
        self.sepet = []
        self.sepet_label = tk.Label(master, text="Sepet: 0 TL", font=FONT, fg=FG_COLOR, bg=BG_COLOR)
        self.sepet_label.pack(pady=5)

        # Butonlar
        btn_frame = tk.Frame(master, bg=BG_COLOR)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Satışı Tamamla", command=self.satisi_tamamla,
                  bg="#27ae60", fg=BTN_FG, font=FONT, width=15).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Ürün Yönetimi", command=self.urun_yonetimi_ekrani,
                  bg="#2980b9", fg=BTN_FG, font=FONT, width=15).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Satış Geçmişi", command=self.satis_gecmisi_penceresi,
                  bg="#9b59b6", fg=BTN_FG, font=FONT, width=15).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Satış Raporu", command=self.satis_raporu,
                  bg="#e67e22", fg=BTN_FG, font=FONT, width=15).grid(row=0, column=3, padx=5)

        self.listele_urunler()

    def listele_urunler(self):
        for w in self.urunler_frame.winfo_children(): w.destroy()
        aranan = self.search_var.get().lower()
        row = col = 0
        for kategori in KATEGORILER:
            cursor.execute("SELECT * FROM urunler WHERE kategori = ?", (kategori,))
            urunler = cursor.fetchall()
            filtre = [u for u in urunler if aranan in u[1].lower()]
            if not filtre: continue
            frm = tk.LabelFrame(self.urunler_frame, text=kategori, font=('Arial', 12, 'bold'),
                                fg=FG_COLOR, bg=CAT_BG, padx=10, pady=10)
            frm.grid(row=row, column=col, padx=10, pady=10, sticky="nw")
            for u in filtre:
                btn = tk.Button(frm, text=f"{u[1]} ({u[2]} TL)", font=FONT,
                                bg=BTN_BG, fg=BTN_FG,
                                command=lambda x=u: self.sepete_ekle(x))
                btn.pack(fill='x', pady=2)
            col += 1
            if col > 4: col = 0; row += 1

    def sepete_ekle(self, urun):
        if urun[4]:
            gram = simpledialog.askfloat("Gramaj", f"{urun[1]} için gram (örnek: 200):")
            if not gram or gram<=0: return
            fiyat = urun[2] * gram/1000
        else:
            fiyat = urun[2]
        self.sepet.append((urun, fiyat))
        toplam = sum(i[1] for i in self.sepet)
        self.sepet_label.config(text=f"Sepet: {toplam:.2f} TL")

    def satisi_tamamla(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for u,f in self.sepet:
            cursor.execute("INSERT INTO satislar(urun_id,tarih,toplam_fiyat) VALUES(?,?,?)",(u[0],now,f))
        conn.commit(); self.sepet.clear(); self.sepet_label.config(text="Sepet: 0 TL")
        messagebox.showinfo("Bilgi","Satış kaydedildi.")

    def urun_yonetimi_ekrani(self):
        top=tk.Toplevel(self.master); top.title("Ürün Ekle/Sil"); top.geometry("400x600"); top.configure(bg=BG_COLOR)
        frm=tk.Frame(top,bg=BG_COLOR); frm.pack(pady=5)
        tk.Label(frm,text="İsim",fg=FG_COLOR,bg=BG_COLOR,font=FONT).grid(row=0,column=0)
        tk.Label(frm,text="Fiyat",fg=FG_COLOR,bg=BG_COLOR,font=FONT).grid(row=1,column=0)
        tk.Label(frm,text="Kategori",fg=FG_COLOR,bg=BG_COLOR,font=FONT).grid(row=2,column=0)
        tk.Label(frm,text="Gramaj Bazlı (1/0)",fg=FG_COLOR,bg=BG_COLOR,font=FONT).grid(row=3,column=0)
        e1=tk.Entry(frm,font=FONT);e2=tk.Entry(frm,font=FONT)
        kv=tk.StringVar(); kv.set(KATEGORILER[0])
        opt=tk.OptionMenu(frm,kv,*KATEGORILER); opt.config(font=FONT,bg=BTN_BG,fg=BTN_FG)
        e3=tk.Entry(frm,font=FONT)
        e1.grid(row=0,column=1); e2.grid(row=1,column=1); opt.grid(row=2,column=1); e3.grid(row=3,column=1)
        def ekle():
            try:
                cursor.execute("INSERT INTO urunler(isim,fiyat,kategori,gramaj_bazli) VALUES(?,?,?,?)",
                               (e1.get(),float(e2.get()),kv.get(),int(e3.get() or 0)))
                conn.commit(); top.destroy(); self.listele_urunler()
            except:
                messagebox.showerror("Hata","Bilgileri kontrol et.")
        tk.Button(frm,text="Ürün Ekle",command=ekle,bg="#27ae60",fg=BTN_FG,font=FONT).grid(row=4,columnspan=2,pady=5)
        canvas=tk.Canvas(top,bg=BG_COLOR,highlightthickness=0)
        scr=tk.Scrollbar(top,orient='vertical',command=canvas.yview)
        cont=tk.Frame(canvas,bg=BG_COLOR)
        cont.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=cont,anchor='nw');canvas.configure(yscrollcommand=scr.set)
        canvas.pack(side='left',fill='both',expand=True);scr.pack(side='right',fill='y')
        tk.Label(cont,text="--- Ürün Sil ---",fg=FG_COLOR,bg=BG_COLOR,font=FONT).pack(pady=5)
        cursor.execute("SELECT * FROM urunler"); items=cursor.fetchall()
        for u in items:
            f=tk.Frame(cont,bg=BG_COLOR); f.pack(fill='x',padx=5,pady=2)
            tk.Label(f,text=f"{u[1]} ({u[2]} TL)",fg=FG_COLOR,bg=BG_COLOR,font=FONT).pack(side='left')
            tk.Button(f,text="Sil",bg="#c0392b",fg=BTN_FG,command=lambda id=u[0]:[cursor.execute("DELETE FROM urunler WHERE id=?",(id,)),conn.commit(),top.destroy(),self.listele_urunler()]).pack(side='right')

    def satis_gecmisi_penceresi(self):
        top=tk.Toplevel(self.master); top.title("Satış Geçmişi"); top.geometry("600x400")
        canvas=tk.Canvas(top,highlightthickness=0);scr=tk.Scrollbar(top,orient='vertical',command=canvas.yview)
        frm=tk.Frame(canvas); frm.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=frm,anchor='nw');canvas.configure(yscrollcommand=scr.set)
        canvas.pack(side='left',fill='both',expand=True);scr.pack(side='right',fill='y')
        cursor.execute("SELECT tarih,urun_id,toplam_fiyat FROM satislar ORDER BY tarih DESC"); data=cursor.fetchall()
        for d in data:
            t,u,f=d;cursor.execute("SELECT isim FROM urunler WHERE id=?",(u,)); name=cursor.fetchone()[0]
            tk.Label(frm,text=f"{t} - {name} - {f:.2f} TL",anchor='w').pack(fill='x',padx=10,pady=2)

    def satis_raporu(self):
        top=tk.Toplevel(self.master); top.title("Satış Raporu"); top.geometry("400x200")
        today=datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT SUM(toplam_fiyat) FROM satislar WHERE tarih LIKE ?",(today+'%',))
        tot=cursor.fetchone()[0] or 0
        cursor.execute("SELECT urun_id,COUNT(*) FROM satislar GROUP BY urun_id ORDER BY COUNT(*) DESC LIMIT 1")
        ec=cursor.fetchone()
        if ec:
            cursor.execute("SELECT isim FROM urunler WHERE id=?",(ec[0],)); ec_name=cursor.fetchone()[0]; ec_count=ec[1]
        else: ec_name="Yok"; ec_count=0
        tk.Label(top,text=f"Bugün Toplam Satış: {tot:.2f} TL",font=('Arial',12)).pack(pady=10)
        tk.Label(top,text=f"En Çok Satılan: {ec_name} ({ec_count} adet)",font=('Arial',12)).pack(pady=5)

    def yenile(self): self.listele_urunler()

if __name__ == '__main__':
    root=tk.Tk(); app=POSUygulama(root); root.mainloop()
