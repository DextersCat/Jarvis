import pyaudio
pa = pyaudio.PyAudio()
for idx in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(idx)
    if info.get('maxInputChannels', 0) > 0:
        print(idx, info.get('name'), info.get('maxInputChannels'))
