import numpy as np
import librosa
import warnings
from scipy.signal import correlate
from scipy.ndimage import median_filter

# 경고 메시지 무시
warnings.filterwarnings("ignore")

# =============================
# [동료의 알고리즘] 기본 전처리 함수들
# =============================

def normalize_audio(vec):
    max_val = np.max(np.abs(vec))
    return vec / max_val if max_val > 0 else vec

def trim_silence(vec, threshold=0.01):
    non_silence = np.where(np.abs(vec) > threshold)[0]
    if len(non_silence) == 0:
        return vec
    return vec[non_silence[0]:non_silence[-1]+1]

def detect_key_chroma(y, sr):
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    return np.argmax(np.mean(chroma, axis=1))

def compute_similarity_over_time(y1, y2, sr, window_sec=1):
    seg_len = int(sr * window_sec)
    total_segments = min(len(y1), len(y2)) // seg_len
    sims = []
    for i in range(total_segments):
        seg1 = y1[i*seg_len:(i+1)*seg_len]
        seg2 = y2[i*seg_len:(i+1)*seg_len]
        if len(seg1) < 1024 or len(seg2) < 1024:
            sims.append(0)
            continue
        c1 = librosa.feature.chroma_cens(y=seg1, sr=sr)
        c2 = librosa.feature.chroma_cens(y=seg2, sr=sr)
        diff = np.mean(np.abs(c1 - c2))
        sim = 1.0 - diff / (np.max([np.std(c1), np.std(c2), 1e-6]) + 1e-6)
        sims.append(sim)
    return np.array(sims)

def find_first_high_similarity_index(sim_vector, threshold=0.75):
    for i, sim in enumerate(sim_vector):
        if sim >= threshold:
            return i
    return 0

def align_by_crosscorr(y1, y2):
    corr = correlate(y1, y2, mode='full')
    lag = np.argmax(corr) - len(y2)
    if lag > 0:
        return y1[lag:], y2[:len(y1)-lag]
    else:
        return y1[:len(y2)+lag], y2[-lag:]

def hybrid_segmental_similarity(y1, y2, sr, segment_sec=1, th_low=0.6):
    seg_len = int(sr * segment_sec)
    total_segments = min(len(y1), len(y2)) // seg_len
    sims = []
    for i in range(total_segments):
        seg1 = y1[i*seg_len:(i+1)*seg_len]
        seg2 = y2[i*seg_len:(i+1)*seg_len]
        if len(seg1) < 1024 or len(seg2) < 1024:
            continue
        c1 = librosa.feature.chroma_cens(y=seg1, sr=sr)
        c2 = librosa.feature.chroma_cens(y=seg2, sr=sr)
        diff1 = np.mean(np.abs(c1 - c2))
        sim1 = 1.0 - diff1 / (np.max([np.std(c1), np.std(c2), 1e-6]) + 1e-6)
        if sim1 < th_low:
            raw_diff = np.mean(np.abs(seg1 - seg2))
            raw_sim = np.exp(-raw_diff * 10)
            sim1 = (sim1 * 0.7) + (raw_sim * 0.3)
        sims.append(sim1)
    return np.array(sims)

def recompare_low_segments(y1, y2, sr, sim_vector, segment_sec=2, threshold=0.6):
    seg_len = int(sr * segment_sec)
    improved = []
    for i, sim in enumerate(sim_vector):
        if sim < threshold:
            seg1 = y1[i*seg_len:(i+1)*seg_len]
            seg2 = y2[i*seg_len:(i+1)*seg_len]
            if len(seg1) < 1024 or len(seg2) < 1024:
                continue
            c1 = librosa.feature.chroma_cens(y=seg1, sr=sr)
            c2 = librosa.feature.chroma_cens(y=seg2, sr=sr)
            min_len = min(c1.shape[1], c2.shape[1])
            c1, c2 = c1[:, :min_len], c2[:, :min_len]
            corr = np.corrcoef(c1.flatten(), c2.flatten())[0, 1]
            corr = np.clip(corr, 0, 1)
            improved.append(corr)
    return np.array(improved)

def autotune_melody_vector_listenable(y, sr):
    f0 = librosa.yin(y, fmin=80, fmax=1000, sr=sr)
    f0 = np.nan_to_num(f0)
    f0_smooth = median_filter(f0, size=7)
    for i in range(1, len(f0_smooth)):
        if f0_smooth[i] <= 1:
            f0_smooth[i] = f0_smooth[i-1]
    hop_length = max(1, int(len(y) / max(1, len(f0_smooth))))
    t_frames = np.arange(len(f0_smooth)) * hop_length
    t = np.arange(len(y))
    freq_interp = np.interp(t, t_frames, f0_smooth)
    phase = 2 * np.pi * np.cumsum(freq_interp) / sr
    tuned = np.sin(phase)
    tuned = median_filter(tuned, size=5)
    tuned = tuned / (np.max(np.abs(tuned)) + 1e-6)
    return tuned

def compare_pitch_sequences(y1, y2, sr):
    f0_1 = librosa.yin(y1, fmin=80, fmax=1000, sr=sr)
    f0_2 = librosa.yin(y2, fmin=80, fmax=1000, sr=sr)
    f0_1, f0_2 = np.nan_to_num(f0_1), np.nan_to_num(f0_2)
    p1 = 12 * np.log2(np.maximum(f0_1, 1e-6) / 440.0)
    p2 = 12 * np.log2(np.maximum(f0_2, 1e-6) / 440.0)
    p1 = (p1 - np.mean(p1)) / (np.std(p1) + 1e-6)
    p2 = (p2 - np.mean(p2)) / (np.std(p2) + 1e-6)
    min_len = min(len(p1), len(p2))
    p1, p2 = p1[:min_len], p2[:min_len]
    corr = np.corrcoef(p1, p2)[0, 1]
    corr = np.clip(corr, 0, 1)
    similarity = corr ** 0.5 
    return similarity * 100

# ==========================================================
# ⭐️ [프론트엔드 연결용 함수] 이 함수가 app.py에서 호출됩니다!
# ==========================================================
def run_analysis(path1, path2):
    print(f"--- 분석 시작: {path1} vs {path2} ---")
    sr = 48000
    
    try:
        # 1. librosa로 오디오 파일 읽기 (동료 코드는 txt를 읽지만, 웹은 mp3를 읽으므로 수정)
        # 60초만 분석 (속도 최적화)
        y1, _ = librosa.load(path1, sr=sr, duration=60, mono=True)
        y2, _ = librosa.load(path2, sr=sr, duration=60, mono=True)
        
        # 2. 전처리 (정규화 및 무음 제거)
        vec1_mono = trim_silence(normalize_audio(y1))
        vec2_mono = trim_silence(normalize_audio(y2))

        # 3. 하모닉·퍼커시브 분리 및 혼합
        y1_h, y1_p = librosa.effects.hpss(vec1_mono)
        y2_h, y2_p = librosa.effects.hpss(vec2_mono)
        y1_mix = 0.7 * y1_h + 0.3 * y1_p
        y2_mix = 0.7 * y2_h + 0.3 * y2_p

        # 4. 키(Key) 맞추기 (Transposition 대응)
        key1 = detect_key_chroma(y1_mix, sr)
        key2 = detect_key_chroma(y2_mix, sr)
        shift_steps = key1 - key2
        y2_shifted = librosa.effects.pitch_shift(y2_mix, sr=sr, n_steps=shift_steps)

        # 5. 시간 동기화 (Sync)
        sim_vector_global = compute_similarity_over_time(y1_mix, y2_shifted, sr, window_sec=1)
        start_idx = find_first_high_similarity_index(sim_vector_global, threshold=0.75)
        start_sample = start_idx * sr
        
        y1_sync = y1_mix[start_sample:]
        y2_sync = y2_shifted[start_sample:]
        y1_sync, y2_sync = align_by_crosscorr(y1_sync, y2_sync)

        # 6. 하이브리드 유사도 계산
        sim_vector = hybrid_segmental_similarity(y1_sync, y2_sync, sr, segment_sec=1, th_low=0.6)
        avg_sim = np.mean(sim_vector) if len(sim_vector) > 0 else 0
        
        # 7. 피치 시퀀스 유사도 (형태 중심)
        y1_auto = autotune_melody_vector_listenable(y1_sync, sr)
        y2_auto = autotune_melody_vector_listenable(y2_sync, sr)
        pitch_sim_pct = compare_pitch_sequences(y1_auto, y2_auto, sr)

        # 8. 최종 점수 산출
        # (평균 유사도와 피치 유사도 중 더 높은 것을 채택하거나 종합)
        avg_sim_pct = avg_sim * 100
        final_score = max(avg_sim_pct, pitch_sim_pct)
        
        # 결과값 정리 (DB에 넣기 위해 리스트로 변환, 너무 길면 자름)
        # 웹 시각화를 위해 100개 포인트로 축소(Downsampling)
        def downsample(arr, n=100):
            if len(arr) < n: return arr.tolist()
            return arr[::len(arr)//n].tolist()

        return round(final_score, 2), downsample(y1_sync), downsample(y2_sync)

    except Exception as e:
        print(f"❌ 분석 오류: {e}")
        # 오류 시 0점 반환
        return 0.0, [], []