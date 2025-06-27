import random
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from . import utils

BASE_DIR = Path('D:/projects/#arrange_psat_problems')
SUBJECTS = ['언어', '자료', '상황']


def run():
    input_filename = utils.get_user_input('입력 파일(xlsx): ', '원본 리스트', str)
    output_filename = utils.get_user_input('출력 파일(xlsx): ', '문제 리스트', str)
    problems_per_round = utils.get_user_input('회차별 문제 수', 10, int)

    input_file = BASE_DIR / f'{input_filename}.xlsx'
    output_file = BASE_DIR / f'{output_filename}.xlsx'

    run_assignment(input_file, output_file, problems_per_round)


def generate_slots(df, problems_per_round=10):
    subject_order = ['언어', '자료', '상황']
    distribution_cycle = [{'언어': 4, '자료': 3, '상황': 3},
                          {'언어': 3, '자료': 4, '상황': 3},
                          {'언어': 3, '자료': 3, '상황': 4}]
    total_problems = len(df)
    total_rounds = int(np.ceil(total_problems / problems_per_round))
    round_ids = list(range(1, total_rounds + 1))

    # (1) 빈 슬롯 구성
    slot_table = []
    for i, r in enumerate(round_ids):
        dist = distribution_cycle[i % 3]
        for subj in subject_order:
            for _ in range(dist[subj]):
                slot_table.append({'회차': r, '과목': subj, '유': None})
    slot_df = pd.DataFrame(slot_table)

    # (2) 유별 개수 적은 순 정렬
    type_counts = df.groupby(['과목', '유']).size().reset_index(name='count')
    type_counts = type_counts.sort_values(by='count', ascending=True)

    # (3) 유별로 회차 분산
    for _, row in type_counts.iterrows():
        subj, typ, cnt = row['과목'], row['유'], row['count']
        shuffled = round_ids.copy()
        random.shuffle(shuffled)

        if cnt <= len(round_ids) // 2:
            stride = max(1, len(round_ids) // cnt)
            offset = random.randint(0, stride - 1)
            chosen = round_ids[offset::stride][:cnt]
        elif cnt < len(round_ids):
            chosen = random.sample(shuffled, cnt)
        elif cnt == len(round_ids):
            chosen = round_ids
        else:
            full = cnt // len(round_ids)
            remainder = cnt % len(round_ids)
            chosen = round_ids * full
            if remainder > 0:
                if remainder <= len(round_ids) // 2:
                    stride = max(1, len(round_ids) // remainder)
                    offset = random.randint(0, stride - 1)
                    chosen += round_ids[offset::stride][:remainder]
                else:
                    chosen += random.sample(shuffled, remainder)
        inserted = 0
        for r in chosen:
            idxs = slot_df[
                (slot_df['회차'] == r) &
                (slot_df['과목'] == subj) &
                (slot_df['유'].isna())
                ].index
            if not idxs.empty:
                slot_df.at[idxs[0], '유'] = typ
                inserted += 1
            if inserted >= cnt:
                break
    return slot_df, total_rounds


def assign_problems_to_slots(df, slot_df):
    df['회차'] = None
    df['번호1'] = None
    df['번호2'] = None

    df_sorted = df.sort_values(by=['과목', '유', '연도', '번호'])
    pool = defaultdict(list)
    for idx, row in df_sorted.iterrows():
        pool[(row['과목'], row['유'])].append(idx)

    local_counter = defaultdict(lambda: defaultdict(int))
    global_counter = defaultdict(int)

    # (1) 슬롯에 문제 배정
    for i, row in slot_df.iterrows():
        key = (row['과목'], row['유'])
        if key in pool and pool[key]:
            idx = pool[key].pop(0)
            round_ = row['회차']
            subj = row['과목']
            local_counter[round_][subj] += 1
            global_counter[round_] += 1
            df.loc[idx, '회차'] = round_
            df.loc[idx, '번호1'] = local_counter[round_][subj]
            df.loc[idx, '번호2'] = global_counter[round_]

    # (2) 보정: 남은 문제로 빈 슬롯 채우기
    slot_missing = slot_df[slot_df['유'].isna()]
    for i, row in slot_missing.iterrows():
        subj = row['과목']
        round_ = row['회차']
        # 과목만 일치하는 남은 문제 찾기
        for key in pool:
            if key[0] == subj and pool[key]:
                idx = pool[key].pop(0)
                slot_df.at[i, '유'] = key[1]
                local_counter[round_][subj] += 1
                global_counter[round_] += 1
                df.loc[idx, '회차'] = round_
                df.loc[idx, '번호1'] = local_counter[round_][subj]
                df.loc[idx, '번호2'] = global_counter[round_]
                break

    # (3) 미배정 문제는 새 회차에 부여
    unassigned = df[df['회차'].isna()]
    if not unassigned.empty:
        next_round = df['회차'].dropna().astype(int).max() + 1
        local = defaultdict(int)
        gnum = 1
        for idx, row in unassigned.iterrows():
            subj = row['과목']
            local[subj] += 1
            df.loc[idx, '회차'] = next_round
            df.loc[idx, '번호1'] = local[subj]
            df.loc[idx, '번호2'] = gnum
            gnum += 1

    return df, slot_df


def create_summary(df):
    counts = pd.pivot_table(df, index='회차', columns='과목', aggfunc='size', fill_value=0)
    counts['총문제수'] = counts.sum(axis=1)
    return counts.reset_index()


def run_assignment(filepath, output_file, problems_per_round=10):
    df = pd.read_excel(filepath)
    df.rename(columns={'괴목': '과목'}, inplace=True)
    df.sort_values(['연도', '번호'], inplace=True)
    slot_df, total_rounds = generate_slots(df, problems_per_round)
    result_df, updated_slot_df = assign_problems_to_slots(df.copy(), slot_df)
    summary_df = create_summary(result_df)
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        result_df.sort_values(by=['#1'], inplace=True)
        result_df.to_excel(writer, sheet_name="문제배정", index=False)
        updated_slot_df.to_excel(writer, sheet_name="슬롯구성", index=False)
        summary_df.to_excel(writer, sheet_name="회차통계요약", index=False)
    return result_df, updated_slot_df, summary_df
