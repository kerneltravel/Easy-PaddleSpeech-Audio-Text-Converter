import os
import logging
import traceback
import paddlespeech
from paddlespeech.cli.asr.infer import ASRExecutor
from paddlespeech.cli.text.infer import TextExecutor
import soundfile
from pydub import AudioSegment
from pathlib import Path

res_path_prefix = Path() / 'conformer_wenetspeech-zh-16k' / 'asr1_conformer_wenetspeech_ckpt_0.1.1.model.tar'
config = os.path.abspath( res_path_prefix / 'model.yaml' )
ckpt_path = os.path.abspath( res_path_prefix / 'exp' / 'conformer' / 'checkpoints' / 'wenetspeech')
wav_time_max_len_second = 50

class MyAudioConverter():
    def __init__(self,asr_executor:ASRExecutor,text_executor=None,wav_time_max_len=50,out_text_dir= "out_text") -> None:
        self.asr_executor = asr_executor
        # self.text_executor = text_executor
        self.wav_time_max_len = wav_time_max_len  # paddlespeech 的音频默认最大支持时长（秒）
        self.out_text_dir = out_text_dir

    def audio_convert_format_to(self, file_from_path, file_to_dir, old_fmt, new_fmt):
        pass

    def convert_audio_part_to_text(self, audio_dir, file_name, file_ext, index, out_dir):
        real_filename = "{}{}{}__{}.{}".format(
            audio_dir, os.sep, file_name, index, file_ext)
        #result = self.asr_executor(audio_file=real_filename,sample_rate=16000,config=config,ckpt_path=ckpt_path,force_yes=True)
        result = self.asr_executor(audio_file=real_filename,sample_rate=16000,force_yes=True)
        out_file_ext = "txt"
        out_text_file = "{}{}{}__{}.{}".format(
            out_dir, os.sep, file_name, index, out_file_ext)
        print(result)
        os.makedirs(name=out_dir, mode=755, exist_ok=True)
        mode = 0o666
        flags = os.O_RDWR | os.O_CREAT
        fd = open(out_text_file, 'w')
        fd.write(result)
        fd.close()
        pass

    def split_audio_by_time_length(self, file_from_path, file_to_dir, max_len) -> bool:
        file_name = ".".join(os.path.basename(
            file_from_path).split(".")[0:-1:])
        file_ext = "".join(os.path.basename(file_from_path).split(".")[-1:])
        sound = AudioSegment.from_wav(file_from_path)
        duration = sound.duration_seconds * 1000  # 音频时长（ms）
        orig_segs = sound.duration_seconds/max_len
        int_segs = int(sound.duration_seconds/max_len)
        out_segs = orig_segs
        avg_len = max_len
        if orig_segs > int_segs:
            out_segs = int_segs+1

        #print("int_segs,out_segs", int_segs, out_segs)

        for i in range(0, out_segs):
            begin = i*(avg_len)*(1000)
            end = (i+1)*(avg_len)*(1000) - 1
            cut_wav = sound[begin:end]
            # print(sound.duration_seconds * 1000, begin,end )
            cut_wav.export(
                file_to_dir + os.sep + "{}__{}.{}".format(file_name, i, file_ext), format='wav')
            audio_dir = file_to_dir
            self.convert_audio_part_to_text(
                audio_dir, file_name, file_ext, i, self.out_text_dir)
        return True

    def convert_audio_to_text(self, file_from_path, file_to_dir) -> bool:
        '''
            convert file_from_path audio file to text files into file_to_dir folder.
            when audio file_from_path time length is longer than max_len seconds (default 50 s), 
            will automatically split into part audio file that is shorter than max_len time.
            
            current only support .wav file. 
            supporting for other format (.mp3, .amr, ) is in progress: convert in background to wav format for TTS.
            
            params:
                file_from_path: audio file path.
                file_to_dir:    output text store dir.

            return value:
                False if file_from_path not exist; 
                True : on other case.
            output:
                text is save as text part file, currently, accroding to file_to_dir .
        '''
        if not os.path.exists(file_from_path):
            return False
        if not os.path.exists(file_to_dir):
            os.makedirs(name=file_to_dir, mode=755, exist_ok=True)
        return self.split_audio_by_time_length(file_from_path, file_to_dir, self.wav_time_max_len)

m = MyAudioConverter(
        asr_executor= ASRExecutor(),
        wav_time_max_len = wav_time_max_len_second
    )
# do convert audio(split to multi-part audio each less then 50-seconds-time) to text in folder "out_audio"
m.convert_audio_to_text("ttsmaker-file-2023-3-19-11-4-33.wav", "out_audio")
