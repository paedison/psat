import random
from collections import Counter

import numpy as np
import pandas as pd


def draw_normal_and_count(n, sample_size=1000, seed=None):
    if seed is not None:
        np.random.seed(seed)

    min_num = random.randint(0, int(n * 0.1))
    max_num = random.randint(int(n * 0.9), n)

    mean = (min_num + max_num) / 2  # 중앙값
    std_dev = max_num / 6  # 표준편차 (대략 99.7%가 0~n 사이에 위치하도록 설정)

    # 정규분포에서 sample_size만큼 실수 추출
    samples = np.random.normal(loc=mean, scale=std_dev, size=sample_size)

    # 0보다 작거나 n보다 큰 값은 제외
    samples = np.clip(samples, min_num, max_num)

    # 정수화 (반올림 or 버림)
    samples = samples.astype(int)

    # 개수 세기
    count = Counter(samples)

    print(f"총 샘플 수: {sample_size}")
    print(f"최솟값: {min_num}")
    print(f"최댓값: {max_num}")
    print(f"정규분포 기반 추출 결과 (평균={mean}, 표준편차={std_dev:.2f}):\n")

    for i in range(min_num, n + 1):
        c = count.get(i, 0)
        ratio = c / sample_size * 100
        print(f"{i}: {c}개 ({ratio:.2f}%)")


# 사용 예시
# draw_normal_and_count(40, sample_size=1000, seed=42)

PROBLEM_COUNTS = {'subject_0': 30, 'subject_1': 40}


def generate_correlated_distributions(max_rate=0.9, sample_size=1000, noise_level=0.1, seed=None):
    if seed is not None:
        np.random.seed(seed)

    def get_max_num(num):
        return random.randint(int(num * max_rate * 0.95), int(num * max_rate))

    max_num_0 = get_max_num(PROBLEM_COUNTS[f'subject_0'])
    max_num_1 = get_max_num(PROBLEM_COUNTS[f'subject_1'])

    # 분포 A: 정규분포 기반, 0~n_a 범위로 클리핑 후 정수화
    mean_0 = max_num_0 / 2
    std_0 = max_num_0 / 6
    dist_0 = np.random.normal(loc=mean_0, scale=std_0, size=sample_size)
    dist_0 = np.clip(dist_0, 0, max_num_0).astype(int)

    # 분포 B: A 값에 비례하지만 noise 추가
    # B 값의 범위는 min_num_1~max_num_b로 제한
    # A를 [0, 1]로 정규화한 뒤 max_num_0로 다시 스케일링, noise_level을 곱한 랜덤잡음 추가
    norm_0 = dist_0 / max_num_0  # A를 0~1로 정규화
    noise = np.random.normal(0, noise_level, size=sample_size)
    dist_1 = (norm_0 + noise) * max_num_1
    dist_1 = np.clip(dist_1, 0, max_num_1).astype(int)

    # 합산 분포
    dist_sum = dist_0 + dist_1

    df = pd.DataFrame({
        'subject_0': dist_0,
        'subject_1': dist_1,
        'subject_sum': dist_sum
    })
    df = df.sort_values('subject_sum', ascending=False)
    return df


def get_frequency_tables_with_relative(df):
    total = len(df)

    # 절대 도수
    freq_0 = df['subject_0'].value_counts().sort_index()
    freq_1 = df["subject_1"].value_counts().sort_index()
    freq_sum = df['subject_sum'].value_counts().sort_index()

    # 상대 도수
    rel_0 = freq_0 / total * 100
    rel_1 = freq_1 / total * 100
    rel_sum = freq_sum / total * 100

    # 하나의 DataFrame으로 통합
    freq_df = pd.DataFrame({
        'subject_0': freq_0,
        'subject_1': freq_1,
        'sum': freq_sum,
        'subject_0_rate': rel_0,
        'subject_1_rate': rel_1,
        'sum_rate': rel_sum,
    }).fillna(0)

    # 정수열은 int로, 상대도수는 소수점 2자리로 포맷팅
    freq_df['subject_0'] = freq_df['subject_0'].astype(int)
    freq_df['subject_1'] = freq_df['subject_1'].astype(int)
    freq_df['sum'] = freq_df['sum'].astype(int)
    freq_df[['subject_0_rate', 'subject_1_rate', 'sum_rate']] = freq_df[
        ['subject_0_rate', 'subject_1_rate', 'sum_rate']].round(2)

    return freq_df


def run():
    df_dict_set = {}
    for i in range(6):
        max_rate = 0.9 - i * 0.03
        df = generate_correlated_distributions(max_rate)
        freq_df = get_frequency_tables_with_relative(df)
        df_dict_set[i] = {'df': df, 'freq_df': freq_df}

    with pd.ExcelWriter('frequency_distribution.xlsx', engine='openpyxl') as writer:
        for i, df_dict in df_dict_set.items():
            df_dict['df'].to_excel(writer, sheet_name=f'distribution_{i}')
            df_dict['freq_df'].to_excel(writer, sheet_name=f'frequency_{i}')


run()