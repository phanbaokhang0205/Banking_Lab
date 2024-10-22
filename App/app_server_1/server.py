from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests, os, socket, threading

app = Flask(__name__)

# Cấu hình cơ sở dữ liệu cho Server 1
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/db_banking'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)

db = SQLAlchemy(app)


# Tự động lấy địa chỉ IP của máy server
def get_server_ip():
    hostname = socket.gethostname()  # Lấy tên máy chủ
    server_ip = socket.gethostbyname(hostname)  # Lấy địa chỉ IP của máy chủ
    return server_ip

server_ip = get_server_ip()

# Mô hình User


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    is_logged_in = db.Column(db.Boolean, default=False)

# Mô hình giao dịch


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_account = db.Column(db.String(80), nullable=False)
    to_account = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# ------------------------------------------------------------------ api----------------------------------------------------------------------------------------
# API đăng nhập


@app.route('/api/login', methods=['POST'])
def login_api():
    _json = request.json
    _username = _json.get('username')
    _password = _json.get('password')

    if _username and _password:
        user = User.query.filter_by(username=_username).first()
        if user:
            if user.password == _password and user.is_logged_in == False:
                user.is_logged_in = True
                db.session.commit()  # Lưu thay đổi vào cơ sở dữ liệu

                # Gửi request đồng bộ tới Server kia
                try:
                    sync_data = {
                        'username': _username,
                        'is_logged': user.is_logged_in,
                    }
                    response = requests.post(
                        f'http://{server_ip}:5002/account_sync', json=sync_data)
                    if response.status_code == 200:
                        return jsonify({'message': 'Transfer successful and synced!'})
                except Exception as e:
                    return jsonify({'error': 'Sync failed: ' + str(e)}), 500
                
                return jsonify({"message": "Login successful", "user_id": user.id, "balance": user.balance}), 200
            else:
                return jsonify({"message": "Invalid password"}), 401
        else:
            return jsonify({"message": "User not found"}), 404
    else:
        return jsonify({"message": "Invalid input"}), 400

# API logout


@app.route('/api/logout', methods=['POST'])
def logout_api():
    data = request.json
    username = data['username']

    user = User.query.filter_by(username=username).first()
    if user:
        user.is_logged_in = False
        db.session.commit()

        # Gửi request đồng bộ tới Server kia
        try:
            sync_data = {
                'username': username,
                'is_logged': user.is_logged_in,
            }
            response = requests.post(
                f'http://{server_ip}:5002/account_sync', json=sync_data)
            if response.status_code == 200:
                return jsonify({'message': 'Transfer successful and synced!'})
            return jsonify({'message': 'Logout successful!'})
        
        except Exception as e:
            return jsonify({'error': 'Sync failed: ' + str(e)}), 500
        
    return jsonify({'error': 'User not found'}), 404


# API chuyển tiền


@app.route('/api/transfer', methods=['POST'])
def transfer_api():
    _json = request.json
    _from = _json.get('from_account')
    _to = _json.get('to_account')
    _amount = float(_json.get('amount'))

    # Lấy thông tin tài khoản
    from_user = User.query.filter_by(username=_from).first()
    to_user = User.query.filter_by(username=_to).first()

    # Kiểm tra số dư
    if from_user and to_user and from_user.balance >= _amount:
        from_user.balance -= _amount
        to_user.balance += _amount

        # Ghi lại giao dịch
        transaction = Transaction(
            from_account=_from, to_account=_to, amount=_amount)
        db.session.add(transaction)
        db.session.commit()

        # Gửi request đồng bộ tới Server 2
        try:
            sync_data = {
                'from_account': _from,
                'to_account': _to,
                'amount': _amount
            }
            response = requests.post(
                f'http://{server_ip}:5002/balance_sync', json=sync_data)
            if response.status_code == 200:
                return jsonify({'message': 'Transfer successful and synced!'})
        except Exception as e:
            return jsonify({'error': 'Sync failed: ' + str(e)}), 500

    return jsonify({'error': 'Transfer failed. Check accounts and balance.'}), 400


# Route đồng bộ dữ liệu từ server 1
@app.route('/balance_sync', methods=['POST'])
def balance_sync():
    data = request.json
    from_account = data['from_account']
    to_account = data['to_account']
    amount = data['amount']

    from_user = User.query.filter_by(username=from_account).first()
    to_user = User.query.filter_by(username=to_account).first()

    if from_user and to_user:
        from_user.balance -= amount
        to_user.balance += amount
        db.session.commit()
        return jsonify({'message': 'Sync successful!'})

    return jsonify({'error': 'Sync failed.'}), 400

# Route đồng bộ dữ liệu từ server 1
@app.route('/account_sync', methods=['POST'])
def account_sync():
    data = request.json
    username = data['username']
    is_logged = data['is_logged']

    user = User.query.filter_by(username=username).first()

    if user:
        user.is_logged_in = is_logged
        db.session.commit()
        return jsonify({'message': 'Sync successful!'})

    return jsonify({'error': 'Sync failed.'}), 400

# get balance
@app.route('/api/user_balance/<username>', methods=['GET'])
def get_user_balance(username):
    user = User.query.filter_by(username=username).first()

    if user:
        return jsonify({'balance': user.balance}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

# ------------------------------------------------------------------UI--------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    with app.app_context():
        db.create_all()
    app.run(debug=True,host=get_server_ip(), port=5000)

