from flask import Flask, render_template, request, redirect
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

def connect_sheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('cider-cloud-XXXXX.json', scope)  # ←認証ファイル名に変更してね
    client = gspread.authorize(creds)
    sheet = client.open('【開発用】シードル出庫台帳')  # ←シート名も合わせてね
    return sheet.worksheet('出庫情報'), sheet.worksheet('出庫詳細')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        出庫日 = request.form['date']
        出庫先 = request.form['destination']
        担当者 = request.form['staff']
        
        出庫情報シート, 出庫詳細シート = connect_sheets()
        
        # 出庫IDを自動生成（出庫情報シートの次の行番号）
        next_row = len(出庫情報シート.get_all_values()) + 1
        出庫ID = str(next_row).zfill(4)

        # 出庫情報を追加
        出庫情報シート.append_row([出庫ID, 出庫日, 出庫先, 担当者])

        # 5商品の情報をループで取得
        for i in range(1, 6):
            商品名 = request.form.get(f'item{i}')
            数量 = request.form.get(f'qty{i}')
            if 商品名 and 数量:
                出庫詳細シート.append_row([出庫ID, 商品名, 数量])

        return redirect('/register')  # 完了後に再表示（また入力できる）

    return render_template('register.html')
