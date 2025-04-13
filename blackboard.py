import mido
from mido import MidiFile
import sounddevice as sd
import numpy as np
from scipy import signal
from scipy.signal import butter, lfilter, sosfilt

def parse_midi(file_path):
    '''
    Parse MIDI file

    :param file_path:
    :return: list containing MIDI information (start_time, duration, pitch)
    '''
    mid = MidiFile(file_path)
    ticks_per_beat = mid.ticks_per_beat
    tempo = 500000

    events = []
    for track in mid.tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            events.append((abs_time, msg))

    # sort the event by absolute time line
    events.sort(key=lambda x: x[0])

    current_time = 0.0
    current_tempo = tempo
    prev_abs_ticks = 0
    active_notes = {}
    notes = []

    for abs_ticks, msg in events:
        delta_ticks = abs_ticks - prev_abs_ticks
        prev_abs_ticks = abs_ticks
        delta_seconds = mido.tick2second(delta_ticks, ticks_per_beat, current_tempo)
        current_time += delta_seconds

        if msg.type == 'set_tempo':
            current_tempo = msg.tempo
        elif msg.type == 'note_on' and msg.velocity > 0:
            key = (msg.channel, msg.note)
            active_notes[key] = current_time
        elif msg.type in ['note_off', 'note_on'] and (msg.velocity == 0 or msg.type == 'note_off'):
            key = (msg.channel, msg.note)
            if key in active_notes:
                start = active_notes.pop(key)
                notes.append((start, current_time - start, msg.note))

    return sorted(notes, key=lambda x: x[0])

# NES STYLE
def generate_audio(notes, sample_rate=44100, noise_ratio=0.1,
                   adsr_params=(0.01, 0.1, 0.7, 0.1)):
    """
    Generate the mix wave including a symple ADSR and noise control

    param：
    - notes: (start_time, duration, pitch)
    - sample_rate: default 44100
    - noise_ratio:（0.0-1.0）
    - adsr_params: (attack_time, decay_time, sustain_level, release_time)

    return：
    audio list
    """
    if not notes:
        return np.zeros(0)

    max_time = max(start + dur for start, dur, _ in notes)
    audio = np.zeros(int(np.ceil(max_time * sample_rate)) + 1)

    attack_time, decay_time, sustain_level, release_time = adsr_params

    # mixed wave ratio, can modify it to simulate NES or other old game console
    wave_ratios = {
        'square': 0.75,
        'triangle': 0.3,
        'noise': noise_ratio
    }




    def lowpass_filter(data, cutoff=2000, order=4):
        nyq = 0.5 * sample_rate
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low')
        return lfilter(b, a, data)
################# NEW FILTER
    def create_crossfade_envelope(crossfade_samples):
        """Create a crossfade envelope using sine interpolation"""
        crossfade_samples = max(0, int(crossfade_samples))
        
        if crossfade_samples <= 0:
            return np.array([]), np.array([])
        
        t = np.linspace(0, np.pi/2, crossfade_samples)
        fade_out = np.sin(t)  # Fade out follows sine curve
        fade_in = np.cos(t)   # Fade in follows cosine curve
        return fade_out, fade_in
    
    prev_note_end_sample = None
    prev_note_end_audio = None


    for start, dur, pitch in notes:
        freq = 440 * 2 ** ((pitch - 69) / 12)
        start_sample = int(start * sample_rate)
        end_sample = int((start + dur) * sample_rate)
        total_samples = end_sample - start_sample
        if total_samples <= 0:
            continue
        t = np.linspace(0, dur, total_samples, False)
        square = 0.6 * signal.square(2 * np.pi * freq * t, duty=0.5) #generate square wave
        triangle = 0.6 * signal.sawtooth(2 * np.pi * freq * t, 0.5) #generate triangle wave
        noise = np.random.normal(0, 0.3, total_samples)
        noise = lowpass_filter(noise, cutoff=3000) * 0.5

        # Control the ratio of different wave.

        mixed = (
                square * wave_ratios['square'] +
                triangle * wave_ratios['triangle'] +
                noise * wave_ratios['noise']
        )




        envelope = np.ones(total_samples)
        attack_samples = min(int(attack_time * sample_rate), total_samples)
        remaining = total_samples - attack_samples
        decay_samples = min(int(decay_time * sample_rate), remaining)
        remaining -= decay_samples
        release_samples = min(int(release_time * sample_rate), total_samples)
        sustain_samples = max(0, total_samples - attack_samples - decay_samples - release_samples)
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        if decay_samples > 0:
            decay_start = attack_samples
            decay_end = decay_start + decay_samples
            envelope[decay_start:decay_end] = np.linspace(1, sustain_level, decay_samples)
        if sustain_samples > 0:
            sustain_start = attack_samples + decay_samples
            envelope[sustain_start:-release_samples] = sustain_level
        if release_samples > 0:
            release_start = max(0, total_samples - release_samples)
            env_slice = envelope[release_start:]
            env_slice *= np.linspace(1, 0, release_samples)
        mixed *= envelope

        crossfade_duration=0.01
        crossfade_samples = int(crossfade_duration * sample_rate)
        
        if prev_note_end_sample is not None:
            # Calculate potential crossfade overlap
            overlap = max(0, start_sample - prev_note_end_sample)
            if overlap > 0 and overlap < crossfade_samples:
                actual_crossfade = min(crossfade_samples, overlap)
                
                # Create crossfade envelopes
                fade_out, fade_in = create_crossfade_envelope(actual_crossfade)
                
                # Crossfade the overlapping region
                crossfade_start = prev_note_end_sample
                crossfade_end = prev_note_end_sample + actual_crossfade
                mixed_start = start_sample
                mixed_end = start_sample + actual_crossfade
                
                # Apply crossfade
                audio[crossfade_start:crossfade_end] *= fade_out
                mixed[:actual_crossfade] *= fade_in

        buffer_end = start_sample + len(mixed)
        if buffer_end > len(audio):
            mixed = mixed[:len(audio) - start_sample]
            buffer_end = len(audio)
        audio[start_sample:buffer_end] += mixed
        
        # Track the end of this note for next iteration's crossfade
        prev_note_end_sample = start_sample + total_samples
        prev_note_end_audio = mixed

        # buffer_end = start_sample + total_samples
        # if buffer_end > len(audio):
        #     mixed = mixed[:len(audio) - start_sample]
        #     buffer_end = len(audio)
        # audio[start_sample:buffer_end] += mixed
    #     Lower the peak noise
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio /= peak * 1.4

    return audio

#GAMEBOY STYLE
def generate_gameboy_audio(notes, sample_rate=44100, 
                          wave_type='square25', noise_mode='periodic',
                          env_attack=0.05, env_decay=0.4, eq_cutoff=2500):
    max_time = max(start + dur for start, dur, _ in notes)
    audio = np.zeros(int(np.ceil(max_time * sample_rate)) + 1)

    # Game Boy wave definition
    GB_WAVEFORMS = {
        'square12':  [15]*4 + [0]*28,
        'square25':  [15]*8 + [0]*24,
        'square50':  [15]*16 + [0]*16,
        'sawtooth':  [0,4,8,12,15,12,8,4]*4,
        'custom':    [8,12,15,12,8,4,0,4]*4
    }
    wave_ratios = {
        'pulse': 0.6,
        'wave': 0.6,
        'noise': 0.8
    }

    # 通道分配函数
    def assign_channel(note_pitch):
        if note_pitch >= 60:
            return 'pulse1'
        elif note_pitch >= 36:
            return 'wave'
        else:
            return 'noise'

    # 预处理波形数据
    wave_samples = np.array(GB_WAVEFORMS[wave_type], dtype=np.float32)
    wave_samples = (wave_samples - 7.5) / 7.5  # 4-bit转-1~1

    # gameboy style filter
    def gameboy_filter(data, cutoff=eq_cutoff, resonance=0.8):
        sos = butter(4, cutoff, 'low', fs=sample_rate, output='sos')
        filtered = signal.sosfilt(sos, data)
        return filtered * resonance

    # processing with each nodes
    for start, dur, pitch in notes:
        freq = 440 * 2 ** ((pitch - 69) / 12)
        channel = assign_channel(pitch)  # 确保channel在此处定义

        # 
        if channel == 'pulse1':
            duty_ratio = {'square12':0.125, 'square25':0.25, 'square50':0.5}[wave_type]
            t = np.linspace(0, dur, int(dur * sample_rate), False)
            wave = 0.4 * signal.square(2 * np.pi * freq * t, duty=duty_ratio)
            wave *= wave_ratios['pulse'] 

        elif channel == 'wave':
            phase = np.arange(int(dur * sample_rate)) * freq / sample_rate
            phase %= 1
            sample_index = (phase * 32).astype(int)
            wave = wave_samples[sample_index] * 0.4
            wave *= wave_ratios['wave'] 

        elif channel == 'noise':
            if noise_mode == 'periodic':
                lfsr = 0x7FFF
                wave = np.zeros(int(dur * sample_rate))
                for i in range(len(wave)):
                    bit = (lfsr ^ (lfsr >> 1)) & 1
                    lfsr = (lfsr >> 1) | (bit << 14)
                    wave[i] = (lfsr & 1) * 2 - 1
                wave = wave * wave_ratios['noise']
            else:
                wave = np.random.normal(0, 0.6, int(dur * sample_rate))
            wave = gameboy_filter(wave, cutoff=eq_cutoff)

        else:  
            continue 

        # 包络处理
        attack_samples = int(env_attack * sample_rate)
        decay_samples = int(env_decay * sample_rate)
        sustain_level = 0.6

        envelope = np.ones_like(wave)
        if attack_samples > 0:
            envelope[:attack_samples] = np.exp(np.linspace(-5, 0, attack_samples))
        if decay_samples > 0:
            decay_start = attack_samples
            decay_end = min(decay_start + decay_samples, len(envelope))
            decay_phase = np.linspace(0, 1, decay_end - decay_start)
            envelope[decay_start:decay_end] = sustain_level + (1 - sustain_level) * np.exp(-5 * decay_phase)

        wave *= envelope

        # mixture the wave
        start_idx = int(start * sample_rate)
        end_idx = start_idx + len(wave)
        if end_idx > len(audio):
            wave = wave[:len(audio)-start_idx]
        audio[start_idx:start_idx+len(wave)] += wave

    # final filter and volumn control
    audio = gameboy_filter(audio, cutoff=eq_cutoff)
    audio = np.clip(audio * 0.9, -1, 1)
    return audio




###########################################################
# C64 STYLE
def generate_c64_audio(notes, sample_rate=44100, 
                      wave_types=['sawtooth', 'pulse', 'triangle'],
                      filter_type='bandpass', filter_cutoff=(800, 5000),
                      sync_channels=[],
                      ring_mod=False, 
                      adsr_params=(0.01, 0.2, 0.7, 0.1)):

    if not notes:
        return np.zeros(0)
    
    max_time = max(start + dur for start, dur, _ in notes)
    audio_length = int(np.ceil(max_time * sample_rate))
    audio = np.zeros(audio_length)
    channels = [np.zeros(audio_length) for _ in range(3)]
    phase_accumulator = 0  # 用于相位连续性


    def generate_wave(freq, duration, wave_type):
        nonlocal phase_accumulator
        if duration <= 0:
            return np.zeros(0)  # 跳过无效时长
        
        n_samples = int(round(duration * sample_rate))  # 统一采样数计算
        t = np.linspace(0, duration, n_samples, endpoint=False)
        
        # 17-bit LFSR噪声生成
        if wave_type == 'noise':
            lfsr = 0x1FFFF
            wave = np.zeros(n_samples)
            for i in range(n_samples):
                bit = (lfsr ^ (lfsr >> 3)) & 1
                lfsr = (lfsr >> 1) | (bit << 16)
                wave[i] = (lfsr & 1) * 2 - 1
            return wave * 0.6

        # 相位连续的正弦波
        phase_increment = freq / sample_rate
        phase = phase_accumulator + np.arange(n_samples) * phase_increment
        phase_accumulator = phase[-1] % 1  # 保存最后相位

        if wave_type == 'pulse':
            wave = 0.6 * signal.square(2 * np.pi * phase, duty=0.5)
        elif wave_type == 'sawtooth':
            wave = 0.6 * signal.sawtooth(2 * np.pi * phase, width=1)
        elif wave_type == 'triangle':
            wave = 0.6 * signal.sawtooth(2 * np.pi * phase, width=0.5)
        else:
            wave = np.zeros(n_samples)
        return wave

    # --------------------------
    # 鲁棒的ADSR包络（强制长度匹配）
    # --------------------------
    def adsr_envelope(duration, attack, decay, sustain_level, release):
        if duration <= 0:
            return np.zeros(0)
        
        n_samples = int(round(duration * sample_rate))  
        attack_samples = min(int(attack * sample_rate), n_samples)
        remaining = n_samples - attack_samples
        
        decay_samples = min(int(decay * sample_rate), remaining)
        remaining -= decay_samples
        
        release_samples = min(int(release * sample_rate), remaining)
        remaining -= release_samples
        
        sustain_samples = max(remaining, 0)
        
        envelope = np.zeros(n_samples)
        # Attack
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        # Decay
        if decay_samples > 0:
            decay_end = attack_samples + decay_samples
            envelope[attack_samples:decay_end] = np.linspace(1, sustain_level, decay_samples)
        # Sustain
        if sustain_samples > 0:
            sustain_start = attack_samples + decay_samples
            envelope[sustain_start:sustain_start+sustain_samples] = sustain_level
        # Release
        if release_samples > 0:
            release_start = n_samples - release_samples
            envelope[release_start:] = np.linspace(sustain_level, 0, release_samples)
        return envelope
#escape useless nodes
    for start, dur, pitch in notes:
        if dur <= 0:  
            continue
            
        freq = 440 * 2 ** ((pitch - 69) / 12)
        channel_id = pitch % 3
        
        wave_type = wave_types[channel_id]
        wave = generate_wave(freq, dur, wave_type)
        
        attack, decay, sustain, release = adsr_params
        envelope = adsr_envelope(dur, attack, decay, sustain, release)
        
        if len(wave) != len(envelope):  # 强制长度匹配
            min_len = min(len(wave), len(envelope))
            wave = wave[:min_len]
            envelope = envelope[:min_len]
        
        if len(wave) == 0:
            continue
            
        wave *= envelope
        
        start_idx = int(start * sample_rate)
        end_idx = start_idx + len(wave)
        if end_idx > len(channels[channel_id]):
            wave = wave[:len(channels[channel_id])-start_idx]
        channels[channel_id][start_idx:start_idx+len(wave)] += wave

    mixed = np.sum(channels, axis=0)
    
    mixed = np.clip(mixed * 0.8, -0.8, 0.8)  # 防止削波
    
    # 带通滤波器
    if filter_type == 'bandpass':
        sos = butter(4, filter_cutoff, 'bandpass', fs=sample_rate, output='sos')
        mixed = sosfilt(sos, mixed)
    
    # 最终音量控制
    peak = np.max(np.abs(mixed))
    return mixed / (peak + 1e-9) * 0.7 if peak > 0 else mixed


# def mode(mode):
#     if mode == 'nes':
#         return generate_audio(notes)
#     elif mode == 'gb':
#         return generate_gameboy_audio(notes,wave_type='square25',noise_mode='periodic',env_attack=0.02,env_decay=0.3)
#     elif mode == 'c64':
#         return 
#     else:
#         continue

if __name__ == '__main__':
    midi_file = 'D:\MIR_mus_sim_vis_sys-main\project\dataset\Lemon-Tree.mid'  # 替换为你的MIDI文件路径
    #midi_file = 'D:\MIR_mus_sim_vis_sys-main\MIR_mus_sim_vis_sys-main\dataset\Super Mario 64 - Medley.mid'
    #midi_file = '\dataset\Lemon-Tree.mid'
    notes = parse_midi(midi_file)
    audio = generate_audio(notes) #NES
    #audio = generate_gameboy_audio(notes,wave_type='square25',noise_mode='periodic',env_attack=0.02,env_decay=0.3)
    audio = generate_c64_audio(notes, wave_types=['sawtooth', 'pulse', 'noise'], filter_cutoff=(800, 5000), adsr_params=(0.01, 0.2, 0.7, 0.1))

    # 播放音频
    sd.play(audio, 44100)
    sd.wait()   