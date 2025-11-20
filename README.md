<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>음성 분석기 - 메인</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <link href="https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    
    <style>
        /* --- 기존 style.css를 보완하는 추가 스타일 --- */
        /* '내 페이지' 섹션용 스타일 */
        .section-divider {
            border: 0;
            height: 1px;
            background-color: #eee;
            margin: 25px 0;
        }
        .sort-controls {
            margin: 20px 0 15px 0;
        }
        .sort-controls span {
            font-weight: bold;
            color: #555;
        }
        .sort-controls select {
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-left: 10px;
            font-family: 'Nanum Gothic', sans-serif;
            background-color: #fff;
        }
        .analysis-history-list {
            list-style-type: none;
            padding-left: 0;
            margin-top: 15px;
        }
        .analysis-history-list li {
            background-color: #f9f9f9;
            border: 1px solid #eee;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.95em;
        }
        .analysis-history-list strong {
            color: #337ab7; /* 포인트 컬러 */
        }
        .similarity-score.high { color: #d9534f; font-weight: bold; }
        .similarity-score.mid { color: #f0ad4e; font-weight: bold; }
        .similarity-score.low { color: #5cb85c; font-weight: bold; }

        .password-change-form {
            margin-top: 20px;
        }
        .password-change-form .input-form-group {
            margin-bottom: 15px;
        }
        .password-change-form label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 0.9em;
            color: #444;
        }
        .form-input-field {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box; /* 너비 계산 용이 */
            font-family: 'Nanum Gothic', sans-serif;
        }
        .password-change-form .detect-btn {
            margin-top: 10px;
        }

        /* '음성 녹음기' 섹션용 스타일 */
        .record-controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }
        .record-controls .detect-btn {
            flex-grow: 1; /* 버튼이 공간을 채우도록 */
        }
        .record-controls .detect-btn:disabled {
            background-color: #ccc;
            border-color: #ccc;
            cursor: not-allowed;
            opacity: 0.7;
        }
        .audio-playback {
            margin-top: 20px;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }
        .audio-playback p {
            font-weight: bold;
            color: #555;
            margin-bottom: 10px;
        }
        .audio-playback #downloadLink {
            background-color: #28a745; /* 다운로드 버튼은 초록색으로 */
            text-align: center;
            display: none; /* JS로 제어 */
            margin-top: 15px; 
            text-decoration: none;
            color: white; /* detect-btn 클래스가 있다면 필요없을 수 있음 */
        }
        .audio-playback #downloadLink:hover {
            background-color: #218838;
        }
    </style>
</head>
<body>
    <div class="main-layout">
        <aside class="sidebar">
            <div class="sidebar-header">
                <h1 class="logo-text-sidebar">Voice Analyze</h1>
                <p class="service-name-sidebar">🎶 음악 표절 검사기</p>
            </div>
            <nav class="sidebar-nav">
                <ul>
                    <li><a href="#" class="nav-item active" data-target="overview-section"><i class="fas fa-home"></i> 홈</a></li>
                    <li><a href="#" class="nav-item" data-target="similarity-section"><i class="fas fa-magnifying-glass-chart"></i> 노래 표절 검사기</a></li>
                    <li><a href="#" class="nav-item" data-target="cover-song-section"><i class="fas fa-music"></i> 커버곡 유사도 검사기</a></li>
                    <li><a href="#" class="nav-item" data-target="record-create-section"><i class="fas fa-microphone-alt"></i> 음성 녹음기 (.mp3)</a></li>
                    <li class="separator"></li> {# 구분선 #}
                    <li><a href="#" class="nav-item" data-target="my-page-section"><i class="fas fa-user"></i> 내 페이지</a></li>
                    <li><a href="#" class="nav-item" data-target="settings-section"><i class="fas fa-cog"></i> 설정</a></li>
                    <li><a href="{{ url_for('login') }}" class="nav-item logout"><i class="fas fa-sign-out-alt"></i> 로그아웃</a></li>
                </ul>
            </nav>
        </aside>

        <main class="content-area">
            <section id="overview-section" class="content-section active">
                <div class="intro-left-section">
                    <h2>음성 유사도 분석으로 <br>당신의 아이디어를 지키세요</h2>
                    <p>
                        저희 서비스는 두 오디오 파일 간의 **특징을 비교**하여, 
                        유사성을 **탐지하고 분석**하는 AI 기반 도구입니다.
                        음악 창작물 또는 음성 콘텐츠의 **독창성 확인**에 도움을 드립니다.
                    </p>
                    <ul class="features">
                        <li><i class="fas fa-check-circle"></i> 두 오디오 파일의 주요 특징 비교</li>
                        <li><i class="fas fa-check-circle"></i> 음성 및 음악 패턴 유사성 분석</li>
                        <li><i class="fas fa-check-circle"></i> 직관적인 분석 결과 제공 (개발 예정)</li>
                    </ul>
                    <div class="rating">
                        <p class="project-status">✨ 기능 개선 및 분석 정확도 향상 작업 중 ✨</p>
                    </div>
                </div>
                <div class="intro-right-image">
                    <div class="placeholder-image">
                        <i class="fas fa-chart-line"></i>
                        <p>음성 분석 시각화</p>
                    </div>
                </div>
            </section>

            <section id="similarity-section" class="content-section">
                <div class="card wide-card">
                    <div class="card-icon">
                        <i class="fas fa-waveform"></i> 
                    </div>
                    <h3>노래 표절 검사기</h3>
                    <p class="card-description">두 개의 원본 노래와 표절 의심 노래를 업로드하여 유사도를 비교합니다.</p>
                    <div class="input-file-group">
                        <input type="text" id="file1-path" placeholder="원본 오디오 파일 (A) 선택" class="file-path-input" readonly>
                        <button class="browse-btn" onclick="document.getElementById('audioFile1').click();">Browse</button>
                        <input type="file" id="audioFile1" style="display: none;" accept="audio/*">
                    </div>
                    <div class="input-file-group">
                        <input type="text" id="file2-path" placeholder="표절 의심 파일 (B) 선택" class="file-path-input" readonly>
                        <button class="browse-btn" onclick="document.getElementById('audioFile2').click();">Browse</button>
                        <input type="file" id="audioFile2" style="display: none;" accept="audio/*">
                    </div>
                    <button class="detect-btn">
                        <i class="fas fa-magnifying-glass"></i> 표절 검사 시작
                    </button>
                </div>
            </section>

            <section id="cover-song-section" class="content-section">
                <div class="card wide-card">
                    <div class="card-icon">
                        <i class="fas fa-music"></i> 
                    </div>
                    <h3>커버곡 유사도 검사기</h3>
                    <p class="card-description">**원본(MR/AR) 파일과 내 커버곡 파일을 업로드하여 유사도를 비교합니다.</p>
                    <div class="input-file-group">
                        <input type="text" id="fileCover1-path" placeholder="원본 MR/AR 파일 선택" class="file-path-input" readonly>
                        <button class="browse-btn" onclick="document.getElementById('audioFileCover1').click();">Browse</button>
                        <input type="file" id="audioFileCover1" style="display: none;" accept="audio/*">
                    </div>
                    <div class="input-file-group">
                        <input type="text" id="fileCover2-path" placeholder="내 커버곡 파일 선택" class="file-path-input" readonly>
                        <button class="browse-btn" onclick="document.getElementById('audioFileCover2').click();">Browse</button>
                        <input type="file" id="audioFileCover2" style="display: none;" accept="audio/*">
                    </div>
                    <button class="detect-btn secondary-btn">
                        <i class="fas fa-check-double"></i> 커버곡 분석 시작
                    </button>
                </div>
            </section>

            <section id="record-create-section" class="content-section">
                <div class="card wide-card">
                    <div class="card-icon">
                        <i class="fas fa-microphone-alt"></i> 
                    </div>
                    <h3>음성 녹음기 (.mp3)</h3>
                    <p class="card-description">마이크를 사용하여 음성을 녹음하고 .mp3 파일로 저장합니다. (현재 .wav/.webm 지원)</p>
                    
                    <div class="record-controls">
                        <button class="detect-btn" id="startRecordBtn">
                            <i class="fas fa-play-circle"></i> 녹음 시작
                        </button>
                        <button class="detect-btn secondary-btn" id="stopRecordBtn" disabled>
                            <i class="fas fa-stop-circle"></i> 녹음 중지
                        </button>
                    </div>

                    <div class="audio-playback" id="playbackContainer" style="display: none;">
                        <p>녹음된 오디오:</p>
                        <audio id="audioPlayback" controls style="width: 100%;"></audio>
                        <a id="downloadLink" class="detect-btn">
                            <i class="fas fa-download"></i> 녹음 파일 다운로드
                        </a>
                    </div>

                </div>
            </section>

            <section id="my-page-section" class="content-section">
                <div class="card wide-card">
                    <h3>내 페이지</h3>
                    <p>안녕하세요, {{ username }}님! 분석 이력을 관리하고 계정 설정을 변경할 수 있습니다.</p>

                    <hr class="section-divider">
                    
                    <h4><i class="fas fa-history"></i> 내 분석 이력</h4>
                    <div class="sort-controls">
                        <span>정렬 기준:</span>
                        <select id="sort-criteria">
                            <option value="date-desc">최신순</option>
                            <option value="date-asc">오래된순</option>
                            <option value="similarity-desc">유사도 높은순</option>
                            <option value="similarity-asc">유사도 낮은순</option>
                        </select>
                    </div>
                    <ul class="analysis-history-list">
                        <li>
                            <div>
                                <strong>[표절 검사]</strong> '내 노래.wav' vs '비교곡.mp3'
                                <br><small style="color: #777;">(2025-11-05 14:30)</small>
                            </div>
                            <span class="similarity-score high">92%</span>
                        </li>
                        <li>
                            <div>
                                <strong>[커버곡 검사]</strong> '원곡MR.mp3' vs '내커버.m4a'
                                <br><small style="color: #777;">(2025-11-04 09:15)</small>
                            </div>
                            <span class="similarity-score mid">78%</span>
                        </li>
                        <li>
                            <div>
                                <strong>[표절 검사]</strong> '데모곡.mp3' vs 'A가수 신곡.mp3'
                                <br><small style="color: #777;">(2025-11-02 18:45)</small>
                            </div>
                            <span class="similarity-score low">15%</span>
                        </li>
                    </ul>

                    <hr class="section-divider">

                    <h4><i class="fas fa-lock"></i> 비밀번호 변경</h4>
                    <form class="password-change-form">
                        <div class="input-form-group">
                            <label for="current-password">현재 비밀번호</label>
                            <input type="password" id="current-password" class="form-input-field" placeholder="현재 비밀번호를 입력하세요">
                        </div>
                        <div class="input-form-group">
                            <label for="new-password">새 비밀번호</label>
                            <input type="password" id="new-password" class="form-input-field" placeholder="새 비밀번호 (8자 이상)">
                        </div>
                        <div class="input-form-group">
                            <label for="confirm-password">새 비밀번호 확인</label>
                            <input type="password" id="confirm-password" class="form-input-field" placeholder="새 비밀번호를 다시 입력하세요">
                        </div>
                        <button type="submit" class="detect-btn">비밀번호 변경</button>
                    </form>
                </div>
            </section>

            <section id="settings-section" class="content-section">
                <div class="card wide-card">
                    <h3>설정</h3>
                    <p>서비스 관련 설정을 변경할 수 있습니다. (개발 예정)</p>
                    <button class="detect-btn secondary-btn">설정 저장</button>
                </div>
            </section>

        </main>
    </div>

    <script>
        // --- 파일 선택 시 경로 표시 스크립트 ---
        document.getElementById('audioFile1').addEventListener('change', function() {
            document.getElementById('file1-path').value = this.files[0] ? this.files[0].name : '';
        });
        document.getElementById('audioFile2').addEventListener('change', function() {
            document.getElementById('file2-path').value = this.files[0] ? this.files[0].name : '';
        });
        
        // (신규) 커버곡 파일 경로 표시
        document.getElementById('audioFileCover1').addEventListener('change', function() {
            document.getElementById('fileCover1-path').value = this.files[0] ? this.files[0].name : '';
        });
        document.getElementById('audioFileCover2').addEventListener('change', function() {
            document.getElementById('fileCover2-path').value = this.files[0] ? this.files[0].name : '';
        });
        // (삭제) 'audioRecord' 리스너 제거

        // --- 사이드바 메뉴 클릭 시 콘텐츠 변경 스크립트 ---
        document.addEventListener('DOMContentLoaded', function() {
            const navItems = document.querySelectorAll('.nav-item');
            const contentSections = document.querySelectorAll('.content-section');

            navItems.forEach(item => {
                item.addEventListener('click', function(e) {
                    // 로그아웃 링크는 기본 동작(페이지 이동)을 허용
                    if (this.classList.contains('logout')) {
                        return; 
                    }
                    
                    e.preventDefault(); // 기본 링크 동작 방지

                    // 모든 nav-item의 active 클래스 제거
                    navItems.forEach(nav => nav.classList.remove('active'));
                    // 클릭된 nav-item에 active 클래스 추가
                    this.classList.add('active');

                    // 모든 content-section 숨기기
                    contentSections.forEach(section => section.classList.remove('active'));
                    
                    // 클릭된 nav-item의 data-target에 해당하는 섹션 보이기
                    const targetId = this.dataset.target;
                    if (targetId) {
                        const targetSection = document.getElementById(targetId);
                        if (targetSection) {
                            targetSection.classList.add('active');
                        }
                    }
                });
            });
        });

        // --- (신규) 음성 녹음기 스크립트 ---
        // (주의: 실제 .mp3 인코딩은 LAME.js 같은 별도 라이브러리가 필요합니다.)
        // 여기서는 MediaRecorder API를 사용한 기본 녹음/재생/다운로드(wav/webm) 로직의 골격을 만듭니다.
        (function() {
            const startBtn = document.getElementById('startRecordBtn');
            const stopBtn = document.getElementById('stopRecordBtn');
            const audioPlayer = document.getElementById('audioPlayback');
            const downloadLink = document.getElementById('downloadLink');
            const playbackContainer = document.getElementById('playbackContainer');
            let mediaRecorder;
            let audioChunks = [];

            startBtn.addEventListener('click', async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    
                    // (참고) MP3를 지원하는지 확인 (대부분 브라우저에서 false)
                    // const options = { mimeType: 'audio/mpeg' };
                    // if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                    //     console.warn('MP3 mimeType is not supported. Falling back to default.');
                    //     options.mimeType = ''; // 기본값 (webm/ogg/wav)
                    // }
                    // mediaRecorder = new MediaRecorder(stream, options);

                    mediaRecorder = new MediaRecorder(stream);
                    
                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = () => {
                        // (참고) 여기서 audioChunks를 MP3 인코더(LAME.js 등)로 보내야 합니다.
                        // 지금은 기본 Blob을 생성합니다.
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' }); 
                        const audioUrl = URL.createObjectURL(audioBlob);
                        
                        audioPlayer.src = audioUrl;
                        downloadLink.href = audioUrl;
                        
                        // 파일명 설정 (mp3 인코딩 시 .mp3로 변경 필요)
                        downloadLink.download = 'recording.wav'; 
                        
                        playbackContainer.style.display = 'block'; // 재생/다운로드 영역 표시
                        audioChunks = []; // 다음 녹음을 위해 초기화
                    };

                    mediaRecorder.start();
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                    playbackContainer.style.display = 'none'; // 녹음 시작 시 숨김

                } catch (err) {
                    console.error("마이크 접근 오류:", err);
                    alert("마이크에 접근할 수 없습니다. 권한을 확인해주세요.");
                }
            });

            stopBtn.addEventListener('click', () => {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                }
            });

            /* // ** .mp3 변환을 위한 참고 **
            // 브라우저 기본 MediaRecorder는 .mp3를 직접 지원하지 않습니다.
            // .mp3로 저장하려면:
            // 1. 'lamejs' 또는 'libmp3lame.js' (WebAssembly) 같은 JS 라이브러리를 HTML에 추가해야 합니다.
            // 2. 녹음이 완료된 후 (onstop) audioBlob의 raw PCM 데이터를 추출합니다.
            // 3. 이 데이터를 MP3 인코더로 전달하여 .mp3 Blob을 생성합니다.
            // 4. 생성된 .mp3 Blob을 다운로드 링크(downloadLink.href)에 연결하고 .download 속성을 'recording.mp3'로 설정합니다.
            // 이는 이 HTML/JS 파일 외부에 추가적인 라이브러리 설정과 복잡한 JS 코딩이 필요합니다.
            */
        })();
    </script>
</body>
</html>
