from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import timedelta, datetime
from flask_mail import Mail, Message 
import os
import random 

# ⭐️ [핵심] 두 개의 분석 파일 불러오기
# 1. 커버곡 분석용 (기존 compare.py)
try:
    from compare import run_analysis as analyze_cover
except ImportError:
    print("⚠️ compare.py (커버곡 분석) 모듈이 없습니다.")
    analyze_cover = None

# 2. 표절 검사용 (새로 만든 plagiarism.py)
try:
    from plagiarism import run_plagiarism_check as analyze_plagiarism
except ImportError:
    print("⚠️ plagiarism.py (표절 검사) 모듈이 없습니다.")
    analyze_plagiarism = None

app = Flask(__name__)

# --- 1. 기본 설정 ---
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=30)

# 파일 업로드 설정
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 제한

# --- 1-1. 이메일 설정 ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'arjkh3301@gmail.com' 
app.config['MAIL_PASSWORD'] = 'crjuiuidcgghbnvg' 
app.config['MAIL_DEFAULT_SENDER'] = 'arjkh3301@gmail.com'

mail = Mail(app)

# --- 1-2. 인증번호 저장소 ---
verification_codes = {} 
reset_codes = {}
 
# --- 2. 데이터베이스 설정 ---
# DB_USER = "postgres"
# DB_PASSWORD = "postgres"
# DB_HOST = "localhost"
# DB_PORT = "5432"
# DB_NAME = "music_db"

# app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

basedir = os.path.abspath(os.path.dirname(__file__))

# 그 폴더 안에 'music_database.db' 라는 파일을 만들어서 DB로 씁니다.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'music_database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 3. 모델 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AnalysisResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 어떤 검사인지 구분하기 위해 type 컬럼을 활용하거나 result_msg에 기록
    file1_path = db.Column(db.String(300), nullable=False)
    file2_path = db.Column(db.String(300), nullable=False)
    vector1 = db.Column(db.JSON, nullable=True)
    vector2 = db.Column(db.JSON, nullable=True)
    similarity_score = db.Column(db.Float, nullable=True)
    result_msg = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

# =========================================================
# 계정 찾기 및 비밀번호 재설정 (기존 유지)
# =========================================================
@app.route('/find-account')
def find_account():
    return render_template('find_account.html')

@app.route('/find-username-proc', methods=['POST'])
def find_username_proc():
    data = request.get_json()
    email = data.get('email')
    if not email: return jsonify({'success': False, 'msg': '이메일을 입력해주세요.'})
    user = User.query.filter_by(email=email).first()
    if user: return jsonify({'success': True, 'username': user.username})
    return jsonify({'success': False, 'msg': '가입된 계정이 없습니다.'})

@app.route('/send-reset-code', methods=['POST'])
def send_reset_code():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    if not username or not email: return jsonify({'success': False, 'msg': '정보를 입력해주세요.'})
    user = User.query.filter_by(username=username, email=email).first()
    if not user: return jsonify({'success': False, 'msg': '일치하는 회원이 없습니다.'})
    
    code = str(random.randint(100000, 999999))
    reset_codes[email] = code 
    try:
        msg = Message("비밀번호 재설정", recipients=[email])
        msg.body = f"인증번호: [{code}]"
        mail.send(msg)
        return jsonify({'success': True, 'msg': '인증번호 발송됨'})
    except Exception as e:
        return jsonify({'success': False, 'msg': f'전송 실패: {e}'})

@app.route('/reset-password-action', methods=['POST'])
def reset_password_action():
    username = request.form.get('username')
    email = request.form.get('email')
    code_input = request.form.get('code')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not all([username, email, code_input, new_password, confirm_password]):
        flash('모든 필드를 입력해주세요.')
        return render_template('find_account.html', active_tab='pw')
    if new_password != confirm_password:
        flash('비밀번호 불일치')
        return render_template('find_account.html', active_tab='pw')
    
    stored_code = reset_codes.get(email)
    if not stored_code or stored_code != code_input:
        flash('인증번호 오류')
        return render_template('find_account.html', active_tab='pw')

    user = User.query.filter_by(username=username, email=email).first()
    if user:
        user.set_password(new_password)
        db.session.commit()
        reset_codes.pop(email, None)
        flash('비밀번호 변경 성공! 로그인해주세요.')
        return redirect(url_for('login'))
    return render_template('find_account.html', active_tab='pw')

# =========================================================
# 로그인 / 회원가입
# =========================================================
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
            flash('아이디 또는 비밀번호 확인 필요')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password-confirm']
        code_input = request.form['email-code'] 

        if password != password_confirm:
            flash('비밀번호 불일치')
            return render_template('register.html', username=username, email=email)
        
        # 인증번호 확인 로직 (필요시 주석 해제)
        stored_code = verification_codes.get(email)
        if not stored_code or stored_code != code_input:
             flash('인증번호 오류')
             return render_template('register.html', username=username, email=email)

        if User.query.filter((User.username==username) | (User.email==email)).first():
            flash('이미 존재하는 회원입니다.')
            return render_template('register.html', username=username, email=email)

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('가입 성공!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/send-code', methods=['POST'])
def send_code():
    data = request.get_json()
    email = data.get('email')
    if not email: return jsonify({'success': False, 'msg': '이메일 입력 필요'})
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'msg': '이미 가입된 이메일'})
    
    code = str(random.randint(100000, 999999))
    verification_codes[email] = code 
    try:
        msg = Message("가입 인증번호", recipients=[email])
        msg.body = f"인증번호: [{code}]"
        mail.send(msg)
        return jsonify({'success': True, 'msg': '발송 완료'})
    except:
        return jsonify({'success': False, 'msg': '전송 실패'})

@app.route('/check-username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get('username')
    if User.query.filter_by(username=username).first():
        return jsonify({'available': False, 'msg': '이미 사용 중'})
    return jsonify({'available': True, 'msg': '사용 가능'})

@app.route('/index')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # ⭐️ [추가된 부분] DB에서 내 분석 기록 가져오기 (최신순 정렬)
    # AnalysisResult 테이블에서 user_id가 내 것인 데이터만 조회
    history = AnalysisResult.query.filter_by(user_id=session['user_id'])\
        .order_by(AnalysisResult.created_at.desc()).all()
        
    # 가져온 history 데이터를 HTML로 전달
    return render_template('index.html', 
                           username=session.get('username'), 
                           history=history)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# =========================================================
# ⭐️ 3. [수정됨] 분석 기능 (두 가지 모드 분리)
# =========================================================

# 공통 파일 저장 함수
def save_uploaded_files(f1, f2):
    filename1 = secure_filename(f1.filename)
    filename2 = secure_filename(f2.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
    p1 = os.path.join(app.config['UPLOAD_FOLDER'], timestamp + filename1)
    p2 = os.path.join(app.config['UPLOAD_FOLDER'], timestamp + filename2)
    f1.save(p1)
    f2.save(p2)
    return p1, p2

# 🅰️ 1. 표절 검사 (plagiarism.py 사용)
@app.route('/analyze-plagiarism', methods=['POST'])
def analyze_plagiarism_route():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    file1 = request.files.get('file1')
    file2 = request.files.get('file2')
    
    if not file1 or not file2:
        flash('파일 두 개가 모두 필요합니다.')
        return redirect(url_for('index'))

    try:
        path1, path2 = save_uploaded_files(file1, file2)

        # plagiarism.py 실행
        if analyze_plagiarism:
            score, vec1, vec2 = analyze_plagiarism(path1, path2)
        else:
            score, vec1, vec2 = 0, [], []
            flash("plagiarism.py 모듈이 없습니다.")

        # 표절 기준 메시지
        msg = "🚨 표절 의심!" if score >= 80 else "✅ 표절 가능성 낮음"

        # DB 저장 (구분을 위해 메시지에 태그 추가)
        result = AnalysisResult(
            user_id=session['user_id'], file1_path=path1, file2_path=path2,
            vector1=vec1, vector2=vec2, similarity_score=score,
            result_msg=f"[표절검사] {msg}"
        )
        db.session.add(result)
        db.session.commit()
        
        return redirect(url_for('result', result_id=result.id))
        
    except Exception as e:
        print(f"Error: {e}")
        flash('분석 중 오류 발생')
        return redirect(url_for('index'))

# 🅱️ 2. 커버곡 검사 (compare.py 사용)
@app.route('/analyze-cover', methods=['POST'])
def analyze_cover_route():
    if not session.get('logged_in'): return redirect(url_for('login'))

    file1 = request.files.get('file1')
    file2 = request.files.get('file2')
    
    if not file1 or not file2:
        flash('파일 두 개가 모두 필요합니다.')
        return redirect(url_for('index'))

    try:
        path1, path2 = save_uploaded_files(file1, file2)

        # compare.py 실행
        if analyze_cover:
            score, vec1, vec2 = analyze_cover(path1, path2)
        else:
            score, vec1, vec2 = 0, [], []
            flash("compare.py 모듈이 없습니다.")

        # 커버곡 기준 메시지
        msg = "🎤 커버곡으로 판명됨" if score >= 60 else "❌ 다른 곡임"

        result = AnalysisResult(
            user_id=session['user_id'], file1_path=path1, file2_path=path2,
            vector1=vec1, vector2=vec2, similarity_score=score,
            result_msg=f"[커버곡검사] {msg}"
        )
        db.session.add(result)
        db.session.commit()
        
        return redirect(url_for('result', result_id=result.id))

    except Exception as e:
        print(f"Error: {e}")
        flash('분석 중 오류 발생')
        return redirect(url_for('index'))

@app.route('/result/<int:result_id>')
def result(result_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    res = AnalysisResult.query.get_or_404(result_id)
    if res.user_id != session['user_id']:
        flash('권한 없음')
        return redirect(url_for('index'))
    return render_template('result.html', data=res)

# ... (위쪽 코드들은 그대로 유지) ...

# ⭐️ [추가] 내 페이지 - 비밀번호 변경 기능 (로그인 상태)
@app.route('/change-password', methods=['POST'])
def change_password():
    # 1. 로그인 체크
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # 2. 입력값 받기
    current_pw = request.form.get('current_password')
    new_pw = request.form.get('new_password')
    confirm_pw = request.form.get('confirm_password')

    # 3. 빈 값 체크
    if not all([current_pw, new_pw, confirm_pw]):
        flash('모든 필드를 입력해주세요.')
        return redirect(url_for('index'))

    # 4. 새 비밀번호 일치 확인
    if new_pw != confirm_pw:
        flash('새 비밀번호가 서로 일치하지 않습니다.')
        return redirect(url_for('index'))

    # 5. 현재 비밀번호가 맞는지 확인 (DB 조회)
    user = User.query.get(session['user_id'])
    
    if not user or not user.check_password(current_pw):
        flash('현재 비밀번호가 올바르지 않습니다.')
        return redirect(url_for('index'))

    # 6. 비밀번호 변경 및 저장
    user.set_password(new_pw)
    db.session.commit()
    
    flash('비밀번호가 성공적으로 변경되었습니다.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)



#업데이트용 아무말