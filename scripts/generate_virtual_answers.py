from pathlib import Path

import numpy as np
import pandas as pd

from . import utils

BASE_DIR = Path('D:/projects/#generate_virtual_answers')
DEFAULT_SUBJECTS = {
    1: ['언어논리', '자료해석', '상황판단'],  # PSAT
    2: ['언어이해', '추리논증'],  # LEET
}

STANDARD_MEANS = {
    '언어논리': 50, '자료해석': 50, '상황판단': 50,
    '언어이해': 45, '추리논증': 60,
}
STANDARD_STDS = {
    '언어논리': 10, '자료해석': 10, '상황판단': 10,
    '언어이해': 10, '추리논증': 10,
}

METRICS = ['맞은 개수', '원점수', '표준점수']
STAT_KEYS = ['최고', '상위10%', '상위25%', '상위50%', '최저', '평균', '표준편차']
BIN_WIDTH = 10


def run():
    exam = utils.get_user_input('시험(1: PSAT, 2: LEET): ', 1, int)
    num_students = utils.get_user_input('학생 수: ', 1000, int)
    input_excel_file = utils.get_user_input('답안 선택률 엑셀 파일명: ', '선택률', str)
    output_excel_file = utils.get_user_input('가상 답안 엑셀 파일명: ', '가상_답안', str)

    subjects = DEFAULT_SUBJECTS.get(exam)
    input_excel = BASE_DIR / f'{input_excel_file}.xlsx'
    output_excel = BASE_DIR / f'{output_excel_file}.xlsx'

    # 결과 저장용
    all_answers, all_scores, all_stats, correct_answers_all = {}, {}, {}, []

    for subject in subjects:
        df = pd.read_excel(input_excel, sheet_name=subject)
        correct_answers, response_array = generate_student_answers(df, num_students)
        score_array, raw_score, std_score = compute_scores(correct_answers, response_array, subject)

        all_answers[subject] = response_array
        all_scores[subject] = {
            '맞은 개수': score_array,
            '원점수': raw_score,
            '표준점수': std_score,
        }

        correct_answers_all.extend([(subject, idx + 1, ans) for idx, ans in enumerate(correct_answers)])

        all_stats[subject] = {k: compute_statistics(all_scores[subject][k]) for k in METRICS}

    # 전체 통계 및 점수 합산
    all_stats['전체'] = {}
    temp_totals = {
        metric: np.sum([all_scores[subject][metric] for subject in subjects], axis=0) for metric in METRICS
    }
    for metric in METRICS:
        all_stats['전체'][metric] = compute_statistics(temp_totals[metric])

    # 학생 정보
    ids = [f'dummy{i:04}' for i in range(1, num_students + 1)]
    passwords = [f'{np.random.randint(0, 10000):04}' for _ in range(num_students)]
    student_info = pd.DataFrame({
        ('학생정보', '이름'): ids,
        ('학생정보', '수험번호'): ids,
        ('학생정보', '비밀번호'): passwords,
    })

    # 학생 답안 시트
    answer_cols = pd.MultiIndex.from_tuples([
        (s, i + 1) for s in subjects for i in range(all_answers[s].shape[1])
    ])
    answers_combined = np.hstack([all_answers[s] for s in subjects])
    answer_df = pd.DataFrame(answers_combined, columns=answer_cols)
    answer_df = pd.concat(
        [student_info[[('학생정보', '이름'), ('학생정보', '수험번호')]], answer_df], axis=1
    )

    # 성적 시트
    score_data = {('학생정보', '이름'): ids, ('학생정보', '수험번호'): ids}
    for metric in METRICS:
        for subject in subjects:
            score_data[(metric, subject)] = all_scores[subject][metric]
        score_data[(metric, '전체')] = temp_totals[metric]
    metric_subject_pairs = [(metric, subject) for metric in METRICS for subject in subjects + ['전체']]
    score_df = pd.DataFrame(score_data)
    score_df.columns = pd.MultiIndex.from_tuples(score_df.columns)
    score_df = score_df[[col for col in metric_subject_pairs]]

    # 정답 시트
    correct_df = pd.DataFrame(correct_answers_all, columns=['과목', '문제', '정답'])

    # 통계 시트
    stat_rows = [
        ((metric, subject), [round(all_stats[subject][metric].get(k, 0), 1) for k in STAT_KEYS])
        for metric in METRICS
        for subject in subjects + ['전체']
    ]
    stat_index = pd.MultiIndex.from_tuples([row[0] for row in stat_rows], names=['지표', '과목'])
    stat_df = pd.DataFrame([row[1] for row in stat_rows], index=stat_index, columns=STAT_KEYS)

    # Excel 저장
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        answer_df.to_excel(writer, sheet_name='학생답안')
        score_df.to_excel(writer, sheet_name='성적')
        correct_df.to_excel(writer, sheet_name='정답')
        stat_df.to_excel(writer, sheet_name='통계')

        # 도수분포표 시트 저장
        for metric in METRICS:
            freq_tables = []
            for subject in subjects + ['전체']:
                values = all_scores[subject][metric] if subject != '전체' else temp_totals[metric]
                bin_width = 1 if metric == '맞은 개수' else BIN_WIDTH
                freq_tables.append(generate_frequency_table(values, subject, bin_width=bin_width))
            freq_df = pd.concat(freq_tables, ignore_index=True)
            freq_df.to_excel(writer, sheet_name=f'{metric}_도수분포', index=False)

    print(f"✅ '{output_excel}' 파일에 모든 시트를 저장했습니다.")


def generate_student_answers(df, num_students):
    correct_answers = df['정답'].tolist()
    probs_matrix = df[['①', '②', '③', '④', '⑤']].div(df[['①', '②', '③', '④', '⑤']].sum(axis=1), axis=0)
    # 각 문제마다 num_students 명의 선택지를 생성
    response_array = np.array([
        np.random.choice([1, 2, 3, 4, 5], size=num_students, p=probs_matrix.iloc[q_idx].values)
        for q_idx in range(len(df))
    ]).T  # 전치하여 (num_students, num_questions) 형태로 만듦
    return correct_answers, response_array


def compute_scores(correct_answers, response_array, subject):
    score_array = (response_array == np.array(correct_answers)).sum(axis=1)
    raw_score = np.round(score_array / len(correct_answers) * 100, 1)
    base_mean = STANDARD_MEANS.get(subject, 50)
    base_std = STANDARD_STDS.get(subject, 10)
    std_score = np.round(
        (score_array - score_array.mean()) / score_array.std() * base_std + base_mean, 1)
    return score_array, raw_score, std_score


def compute_statistics(values):
    return {
        '평균': values.mean(),
        '표준편차': values.std(),
        '최고': values.max(),
        '최저': values.min(),
        '상위10%': np.percentile(values, 90),
        '상위25%': np.percentile(values, 75),
        '상위50%': np.percentile(values, 50),
    }


def generate_frequency_table(values: np.ndarray, subject: str, bin_width: int = 10) -> pd.DataFrame:
    """구간 기반 도수분포표 생성 함수

    Args:
        values (np.ndarray): 학생 점수 데이터
        subject (str): 과목명 (혹은 '전체')
        bin_width (int, optional): 구간 너비. 기본값은 10

    Returns:
        pd.DataFrame: [과목, 구간, 빈도수] 형태의 도수분포표
    """
    series = pd.Series(values)
    min_val, max_val = int(series.min()), int(series.max()) + 1
    start_bin = (min_val // bin_width) * bin_width
    end_bin = ((max_val // bin_width) + 1) * bin_width
    bins = list(range(start_bin, end_bin + 1, bin_width))

    # 구간 라벨 생성
    labels = [f'{b}점 이상~{b + bin_width}점 미만' for b in bins[:-1]]

    binned = pd.cut(series, bins=bins, labels=labels, right=False)
    freq = binned.value_counts().sort_index()
    freq_df = freq.rename_axis('구간').reset_index(name='빈도수')
    freq_df.insert(0, '과목', subject)

    return freq_df
