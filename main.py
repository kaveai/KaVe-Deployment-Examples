from flask import Flask, render_template, request
import os
import re
import time
import numpy as np
import pandas as pd
import pickle
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3
from os.path import join, dirname, realpath

app = Flask(__name__)
UPLOADS_PATH = join(dirname(realpath(__file__)), 'static/uploads/')


veri = pd.read_excel(UPLOADS_PATH+"df.xlsx")

#--------------------TANIMLAR VE FONKSİYONLAR-----------------------#
class yasamkocum():

    def __init__(self, veri):
        self.veri = veri

    def benzerlik(self, A, B):
        """
        Jaccard benzerligi
        """
        A = [a.lower() for a in A.split()]
        B = [b.lower() for b in B.split()]

        A_kesisim_B = {a for a in A if a in B}
        A_kesisim_B_sayisi = len(A_kesisim_B)
        A_birlesim_B_sayisi = len(A) + len(B) - len(A_kesisim_B)
        return A_kesisim_B_sayisi / A_birlesim_B_sayisi

    def tavsiye(self, secim = "idare"):
        """
        Secilen kategoride rastgele tavsiye
        """
        filtre = self.veri[self.veri.kategori == secim]
        return filtre.Sozler.sample(n=1).values[0]

    def dinle_ve_tavsiye_ver(self, user_inputs):
        cevap = user_inputs.lower()

        if cevap in set(self.veri.kategori):
            return self.tavsiye(secim = cevap)
        else:
            f = lambda x: self.benzerlik(x, cevap)
            sonuc = self.veri.Sozler.apply(f)
            # sonuc_idx = sonuc.sort_values(ascending=False).index[0]
            return self.veri.iloc[sonuc.idxmax()].Sozler
#--------------------TANIMLAR VE FONKSİYONLAR-----------------------#
#----------------------------YAŞAM KOÇUM----------------------------#
@app.route('/process')
def process():
    user_input=request.args.get('user_input')
    user_nick=request.args.get('user_nick')
    db = sqlite3.connect(UPLOADS_PATH+"full.db")
    cs = db.cursor()
    koc = yasamkocum(veri)
    bot_response= koc.dinle_ve_tavsiye_ver(user_input)
    bot_response=str(bot_response)
    cs.execute("""INSERT INTO datas(user_nick,user_input,bot_response) VALUES (?,?,?)""",(user_nick,user_input,bot_response))
    db.commit()
    db.close()
    return str(bot_response)

@app.route('/yasam-kocum-base')
def yasam_kocum():
    return render_template('yasam-kocum.html')

@app.route('/yasam-kocum',methods=['POST'])
def login_verification():
    try:
        user_nick=request.form['user_nick']
        user_pass=request.form['user_pass']
        db = sqlite3.connect(UPLOADS_PATH+"full.db")
        cs = db.cursor()
        user_real_pass = cs.execute("SELECT user_password FROM userdb WHERE user_nick=?", (user_nick,)).fetchall()[0][0]
        
        if user_real_pass == user_pass:
            return render_template('yasam-kocum.html', user_nick=user_nick)
        else:
            return render_template('login.html', alert = "Hatalı Parola")
    except IndexError:
        return render_template('login.html', alert = "Kullanıcı Adı Tanınmadı, Doğru Yazdığınızdan Emin Olun.")

#----------------------------YAŞAM KOÇUM----------------------------#
#----------------------------GİRİŞ SAYFALARI------------------------#
@app.route('/')
def login_home():
    return render_template('login.html')

@app.route('/sign-up',methods=['POST'])
def signup():
    db = sqlite3.connect(UPLOADS_PATH+"full.db")
    cs = db.cursor()
    user_nick= request.form['user_nick_signup']
    user_pass = request.form['user_pass_signup']
    user_mail = request.form['email_signup']
    if len(cs.execute("SELECT user_password FROM userdb WHERE user_nick=?", (user_nick,)).fetchall()) == 0:
        cs.execute("""INSERT INTO userdb(user_nick,user_password,user_email) VALUES (?,?,?)""",(user_nick,user_pass,user_mail))
        db.commit()
        db.close()
        return render_template('yasam-kocum.html', user_nick=user_nick)
    else:
        return render_template('login.html', alert="Böyle Bir Kullanıcı Zaten Bulunuyor.")
#----------------------------GİRİŞ SAYFALARI------------------------#



#-----------------------------EV KREDİSİ----------------------------#
@app.route('/ev-kredisi')
def index():
    return render_template('ev-kredisi.html',sonuc_basari="", sonuc_olumsuz="")

@app.route('/sonuc',methods=['POST'])
def sonuc():
    model = pickle.load(open(UPLOADS_PATH+'base-model.sav', 'rb'))

    input_1 = request.form['EXT_SOURCE_3']
    input_2 = request.form['DAYS_LAST_PHONE_CHANGE']
    input_3 = request.form['DAYS_CREDIT']
    input_4 = request.form['EXT_SOURCE_2']
    input_5 = request.form['AMT_CREDIT_x']
    input_6 = request.form['AMT_ANNUITY_x']

    input_array = np.array([float(input_1),float(input_2),float(input_3),float(input_4),float(input_5),float(input_6)])
    input_array = input_array.reshape(1, -1)
    y_pred = model.predict(input_array)

    
    if y_pred == 1:
        return render_template('ev-kredisi.html',sonuc_basari="Krediniz Onaylanmıştır.",sonuc_olumsuz="")

    if y_pred == 0:
        return render_template('ev-kredisi.html',sonuc_olumsuz="Krediniz Onaylanmamıştır.",sonuc_basari="")
#-----------------------------EV KREDİSİ----------------------------#


#-----------------------------ZİNGAT M2----------------------------#
@app.route('/zingat-fiyatlama')
def zingat():
    return render_template('zingat-m2.html',sonuc_m2="")

@app.route('/zingat-sonuc',methods=['POST'])
def zingat_sonuc():
    model = pickle.load(open(UPLOADS_PATH+'zingat-model.sav', 'rb'))

    input_1 = request.form['sehir']
    if input_1.lower() == "istanbul":
        input_1 = 1
    elif input_1.lower() == "ankara":
        input_1 = 2
    else:
        input_1 = 3

    input_2  = request.form['ilce']
    input_3  = request.form['mahalle']
    # Veri az olduğu için rastgele değerler atayacağız. 
    input_2 = np.random.randint(1,4)
    input_3 = np.random.randint(1,86)


    input_4  = int(request.form['kat_bilgisi'])
    input_5  = int(request.form['oda_sayisi'])
    input_6  = int(request.form['lavabo_sayisi'])
    input_7  = request.form['kombi_durumu']

    if input_7.lower() == "evet" or "var":
        input_7 = 1
    else:
        input_7 = 0
    
    input_8  = request.form['balkon_durumu']

    if input_8.lower() == "evet" or "var":
        input_8 = 1
    else:
        input_8 = 0

    input_9 = int(request.form['m2'])
    m2 = input_9
    if input_9 <= 80:
        input_9 = 0
    elif input_9 > 80 and input_9 <= 130:
        input_9 = 1
    elif input_9 > 130:
        input_9 = 2

    input_array = np.array([input_1,input_2,input_3,input_4,input_5,input_6,input_7,input_8,input_9])
    input_array = input_array.reshape(1, -1)
    sonuc_m2 = model.predict(input_array)

    return render_template('zingat-m2.html',sonuc_m2=int(sonuc_m2[0].round(2)), total_fiyat=int((sonuc_m2[0])*m2))
#-----------------------------ZİNGAT M2----------------------------#

#-----------------------------İŞE ALIM----------------------------#
@app.route('/ise-alim')
def ise_alim():
    return render_template('ise-alim.html',sonuc_basari="", sonuc_olumsuz="")

@app.route('/is-sonuc', methods=['POST'])
def ise_alim_sonuc():
    model = pickle.load(open(UPLOADS_PATH+'knn-model.sav', 'rb'))

    input_1 = request.form['social']
    input_2 = request.form['algorithm']
    input_3 = request.form['gpa']
    input_4 = request.form['age']

    input_4 = int(input_4) / 10

    input_array = np.array([input_1,input_2,input_3,input_4])
    input_array = input_array.reshape(1, -1)
    y_pred = model.predict(input_array)

    if y_pred == 1:
        return render_template('ise-alim.html',sonuc_basari="İşe Alım Simülasyonunu Başarıyla Geçtiniz",sonuc_olumsuz="")

    if y_pred == 0:
        return render_template('ise-alim.html',sonuc_olumsuz="İşe Alım Simülasyonunu Maalesef Geçemediniz.",sonuc_basari="")

#-----------------------------İŞE ALIM----------------------------#
if __name__=='__main__':
	app.run(debug=False,port=85)