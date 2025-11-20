from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from flask_mail import Mail, Message 
import os
import random 


app = Flask(__name__)

# --- 1. 기본 설정 ---
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=30)

# --- ⭐️ 1-1. 이메일(SMTP) 설정 ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'arjkh3301@gmail.com' 
app.config['MAIL_PASSWORD'] = 'crjuiuidcgghbnvg' 
app.config['MAIL_DEFAULT_SENDER'] = 'arjkh3301@gmail.com'

mail = Mail(app)

# --- ⭐️ 1-2. 임시 인증번호 저장소 ---
verification_codes = {} 

# --- 2. 데이터베이스 설정 (PostgreSQL) ---
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "music_db"

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 3. 데이터베이스 모델 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- 4. 라우팅 ---

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['logged_in'] = True
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            flash('잘못된 사용자 이름 또는 비밀번호입니다.')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/send-code', methods=['POST'])
def send_code():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'msg': '이메일을 입력해주세요.'})

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({'success': False, 'msg': '이미 가입된 이메일입니다.'})

    code = str(random.randint(100000, 999999))
    verification_codes[email] = code 

    try:
        msg = Message("Voice Analyze 회원가입 인증번호", recipients=[email])
        msg.body = f"인증번호는 [{code}] 입니다. 회원가입 화면에 입력해주세요."
        mail.send(msg)
        return jsonify({'success': True, 'msg': '인증번호가 발송되었습니다! 메일함을 확인하세요.'})
    except Exception as e:
        print(f"❌ 이메일 전송 에러: {e}")
        return jsonify({'success': False, 'msg': f'전송 실패: {str(e)}'})

# ⭐️ [추가] 아이디 중복 확인 전용 API (버튼 클릭 시 동작)
@app.route('/check-username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'available': False, 'msg': '아이디를 입력해주세요.'})
    
    # DB에서 아이디로 조회
    user = User.query.filter_by(username=username).first()
    
    if user:
        return jsonify({'available': False, 'msg': f"'{username}'은(는) 이미 사용 중인 아이디입니다."})
    else:
        # 사용자가 공백을 섞어 썼더라도, 실제로는 공백 없는 버전으로 안내
        return jsonify({'available': True, 'msg': f"'{username}'은(는) 사용 가능한 아이디입니다."})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password-confirm']
        code_input = request.form['email-code'] 

        # ⭐️ 에러 발생 시 redirect가 아니라 render_template를 사용하여 입력값(username, email 등)을 다시 보냄

        # 1. 비밀번호 확인
        if password != password_confirm:
            flash('비밀번호가 일치하지 않습니다.')
            return render_template('register.html', username=username, email=email, code_input=code_input)

        # 2. 중복 확인
        if User.query.filter_by(username=username).first():
            flash('이미 존재하는 사용자 이름입니다.')
            return render_template('register.html', username=username, email=email, code_input=code_input)
        
        if User.query.filter_by(email=email).first():
            flash('이미 사용 중인 이메일입니다.')
            return render_template('register.html', username=username, email=email, code_input=code_input)

        # 3. 인증번호 검증
        stored_code = verification_codes.get(email)
        
        if not stored_code:
            flash('인증번호 전송 버튼을 먼저 눌러주세요.')
            return render_template('register.html', username=username, email=email, code_input=code_input)
        
        if stored_code != code_input:
            flash('인증번호가 틀렸습니다. 다시 확인해주세요.')
            return render_template('register.html', username=username, email=email, code_input=code_input)

        # 4. 검증 성공 -> DB 저장
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        del verification_codes[email]
        
        flash('회원가입 성공! 로그인해주세요.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/index')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)