from flask import Flask, render_template, request, redirect, url_for
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

def connect_sheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('cider-cloud.json', scope)  # ←認証ファイル名に変更してね
    client = gspread.authorize(creds)
    sheet = client.open('【開発用】シードル出庫台帳')  # ←シート名も合わせてね
    return sheet.worksheet('出庫情報'), sheet.worksheet('出庫詳細')

def generate_unique_id(出庫情報シート):
    today_str = datetime.datetime.now().strftime("%y%m%d")
    all_ids = [row[0] for row in 出庫情報シート.get_all_values()[1:] if row[0].startswith(today_str)]
    counter = len(all_ids) + 1
    return f"{today_str}-{str(counter).zfill(3)}"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        出庫日 = request.form['date']
        出庫先 = request.form['destination']
        担当者 = request.form['staff']
        取引先 = request.form.get('client', '')  # ← 追加欄、空欄OK

        出庫情報シート, 出庫詳細シート = connect_sheets()
        出庫ID = generate_unique_id(出庫情報シート)


        # ✅ シートの列順に合わせて書き込み（出庫ID, 出庫日, 出庫先, 取引先, 担当者）
        出庫情報シート.append_row([出庫ID, 出庫日, 出庫先, 取引先, 担当者])

        for i in range(1, 6):
            商品名 = request.form.get(f'item{i}')
            数量 = request.form.get(f'qty{i}')
            if 商品名 and 数量:
                出庫詳細シート.append_row([出庫ID, 商品名, 数量])

        return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/list')
def list_data():
    出庫情報シート, _ = connect_sheets()  # ← 出庫詳細シートは使わない

    出庫情報 = 出庫情報シート.get_all_values()

    return render_template('list.html', 出庫情報=出庫情報)

@app.route('/detail/<shukko_id>')
def detail(shukko_id):
    出庫情報シート, 出庫詳細シート = connect_sheets()

    # 出庫情報の該当行だけ取得（ヘッダー除いて検索）
    出庫情報リスト = 出庫情報シート.get_all_values()
    出庫情報 = next((row for row in 出庫情報リスト if row[0] == shukko_id), None)

    # 出庫詳細の該当行をすべて取得
    出庫詳細リスト = 出庫詳細シート.get_all_values()
    出庫詳細 = [row for row in 出庫詳細リスト if row[0] == shukko_id]

    return render_template('detail.html', 出庫情報=出庫情報, 出庫詳細=出庫詳細, 出庫ID=shukko_id)


@app.route('/edit/<shukko_id>', methods=['GET', 'POST'])
def edit(shukko_id):
    出庫情報シート, _ = connect_sheets()
    出庫情報リスト = 出庫情報シート.get_all_values()

    # 該当行のインデックスとデータを取得
    index = None
    出庫情報 = None
    for i, row in enumerate(出庫情報リスト):
        if row[0] == shukko_id:
            index = i + 1  # Sheetsは1始まり
            出庫情報 = row
            break

    if request.method == 'POST':
        出庫日 = request.form['date']
        出庫先 = request.form['destination']
        取引先 = request.form['client']
        担当者 = request.form['staff']

        出庫情報シート.update(f'B{index}:E{index}', [[出庫日, 出庫先, 取引先, 担当者]])
        return redirect(url_for('list_data'))


    return render_template('edit.html', 出庫ID=shukko_id, 出庫情報=出庫情報)

@app.route('/edit-detail/<shukko_id>', methods=['GET', 'POST'])
def edit_detail(shukko_id):
    _, 出庫詳細シート = connect_sheets()
    出庫詳細リスト = 出庫詳細シート.get_all_values()

    # 該当する出庫詳細だけ取り出す
    対象行 = []
    for i, row in enumerate(出庫詳細リスト):
        if row[0] == shukko_id:
            対象行.append({
                "index": i + 1,  # Sheetsは1始まり
                "商品名": row[1],
                "数量": row[2]
            })

    if request.method == 'POST':
        for i, item in enumerate(対象行):
            商品名 = request.form.get(f'item{i}')
            数量 = request.form.get(f'qty{i}')
            if 商品名 and 数量:
                出庫詳細シート.update(f'B{item["index"]}:C{item["index"]}', [[商品名, 数量]])
        return redirect(url_for('edit', shukko_id=shukko_id))

    return render_template('edit_detail.html', 出庫ID=shukko_id, 出庫詳細=対象行)




if __name__ == '__main__':
    app.run(debug=True)
