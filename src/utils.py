def time_convert(seconds):
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h}г {m}хв {s}с"