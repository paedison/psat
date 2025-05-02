from pathlib import Path

import numpy as np
import pandas as pd

from . import utils

BASE_DIR = Path('D:/projects/#generate_virtual_answers')
DEFAULT_SUBJECTS = {
    0: ['subject_0', 'subject_1'],  # LEET
    1: ['subject_0', 'subject_1', 'subject_2', 'subject_3'],  # PSAT 5급
    2: ['subject_1', 'subject_2', 'subject_3'],  # PSAT 7급
}

STANDARD_BASE_MEANS = {
    0: {'subject_0': 45, 'subject_1': 60},
    1: {'subject_0': 50, 'subject_1': 50, 'subject_2': 50, 'subject_3': 50},
    2: {'subject_1': 50, 'subject_2': 50, 'subject_3': 50},
}

STANDARD_BASE_STDS = {
    0: {'subject_0': 10, 'subject_1': 10},
    1: {'subject_0': 10, 'subject_1': 10, 'subject_2': 10, 'subject_3': 10},
    2: {'subject_1': 10, 'subject_2': 10, 'subject_3': 10},
}

METRICS = ['맞은 개수', '원점수', '표준점수']
STAT_KEYS = ['max', 't10', 't25', 't50', 'min', 'avg', 'std']
BIN_WIDTH = 10


def run():
    exam = utils.get_user_input('시험(0: LEET, 1: PSAT 5급, 2: PSAT 7급): ', 0, int)
    num_students = utils.get_user_input('학생 수: ', 1000, int)
    input_excel_file = utils.get_user_input('답안 선택률 엑셀 파일명: ', '선택률', str)
    output_excel_file = utils.get_user_input('가상 답안 엑셀 파일명: ', '가상_답안', str)

    subjects = DEFAULT_SUBJECTS.get(exam)
    subjects_plus_total = subjects + ['total']
    input_excel = BASE_DIR / f'{input_excel_file}.xlsx'
    output_excel = BASE_DIR / f'{output_excel_file}.xlsx'

    # 결과 저장용
    all_correct_answers, all_answers, all_scores, all_stats,  = [], {}, {}, {}

    for subject in subjects:
        df = pd.read_excel(input_excel, sheet_name=subject)
        correct_answers = df['정답'].tolist()
        response_array = generate_student_answers(df, num_students)
        score_array, raw_score_array, std_score_array = compute_scores(
            correct_answers, response_array, exam, subject)

        all_answers[subject] = response_array
        all_scores[subject] = {
            '맞은 개수': score_array,
            '원점수': raw_score_array,
            '표준점수': std_score_array,
        }

        all_correct_answers.extend([(subject, idx + 1, ans) for idx, ans in enumerate(correct_answers)])

        all_stats[subject] = {k: compute_statistics(all_scores[subject][k]) for k in METRICS}

    # 정답 시트
    correct_answer_df = pd.DataFrame(all_correct_answers, columns=['subject', 'number', 'answer'])

    # 전체 통계 및 점수 합산
    all_stats['total'] = {}
    temp_totals = {
        metric: np.sum([all_scores[subject][metric] for subject in subjects], axis=0) for metric in METRICS
    }
    for metric in METRICS:
        all_stats['total'][metric] = compute_statistics(temp_totals[metric])

    # 학생 정보
    ids = [f'dummy{i:04}' for i in range(1, num_students + 1)]
    passwords = [f'{np.random.randint(0, 10000):04}' for _ in range(num_students)]
    student_df = pd.DataFrame({('student', 'serial'): ids, ('student', 'password'): passwords})

    # 학생 답안 시트
    answer_cols = pd.MultiIndex.from_tuples([
        (s, i + 1) for s in subjects for i in range(all_answers[s].shape[1])
    ])
    answers_combined = np.hstack([all_answers[s] for s in subjects])
    answer_df = pd.DataFrame(answers_combined, columns=answer_cols)
    answer_df = pd.concat([student_df, answer_df], axis=1)

    # 성적 시트
    score_data = {}
    for metric in METRICS:
        for subject in subjects:
            score_data[(metric, subject)] = all_scores[subject][metric]
        score_data[(metric, 'total')] = temp_totals[metric]

        # 등수 계산 및 score_data에 추가
        for subject in subjects_plus_total:
            values = all_scores[subject]['맞은 개수'] if subject != 'total' else temp_totals['맞은 개수']
            score_data[('등수', subject)] = get_descending_ranks(values)

    score_df = pd.DataFrame(score_data)
    score_df.columns = pd.MultiIndex.from_tuples(score_df.columns)
    score_df = pd.concat([student_df, score_df], axis=1)

    # 통계 시트
    stat_rows = [
        ((m, s), [round(all_stats[s][m].get(k, 0), 1) for k in STAT_KEYS])
        for m in METRICS for s in subjects_plus_total
    ]
    stat_index = pd.MultiIndex.from_tuples([row[0] for row in stat_rows], names=['metric', 'subject'])
    stat_df = pd.DataFrame([row[1] for row in stat_rows], index=stat_index, columns=STAT_KEYS)

    # 도수분포표 시트
    freq_rows = []
    for metric in METRICS:
        for subject in subjects_plus_total:
            values = all_scores[subject][metric] if subject != 'total' else temp_totals[metric]
            bin_width = 1 if metric == '맞은 개수' else BIN_WIDTH
            freq_df = generate_frequency_table(values, subject, bin_width=bin_width)
            for _, row in freq_df.iterrows():
                freq_rows.append((metric, row['subject'], row['bin'], row['frequency']))
    freq_df = pd.DataFrame(freq_rows, columns=['metric', 'subject', 'bin', 'freq'])
    freq_df.set_index(['metric', 'subject', 'bin'], inplace=True)

    # 문항별 답안 선택률 시트
    choice_all = []
    for subject in subjects:
        response_array = all_answers[subject]
        answer_count_df = calculate_answer_distribution(response_array)
        answer_count_df.insert(0, 'subject', subject)
        answer_count_df.insert(1, 'number', answer_count_df.index)
        choice_all.append(answer_count_df.reset_index(drop=True))
    answer_count_df = pd.concat(choice_all, ignore_index=True)

    # 등수 기반 그룹별 답안 선택 개수 시트
    group_choice_counts_all = {'top': [], 'mid': [], 'low': []}
    for subject in subjects:
        response_array = all_answers[subject]
        ranks = get_descending_ranks(all_scores[subject]['맞은 개수'])
        group_choice_counts = create_groupwise_answer_counts_by_rank(response_array, ranks)

        for group_name in ['top', 'mid', 'low']:
            df = group_choice_counts[group_name]
            df.insert(0, 'number', df.index)  # 문항번호 추가
            df.insert(0, 'subject', subject)  # 과목 추가
            df.reset_index(drop=True, inplace=True)
            group_choice_counts_all[group_name].append(df)

    # Excel 저장
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        # 정답 시트, 학생 답안 시트, 선택률 시트, 성적 시트, 통계 시트 저장
        correct_answer_df.to_excel(writer, sheet_name='correct_answer')
        answer_df.to_excel(writer, sheet_name='answer')
        score_df.to_excel(writer, sheet_name='score')
        stat_df.to_excel(writer, sheet_name='statistics')
        freq_df.to_excel(writer, sheet_name='frequency')
        answer_count_df.to_excel(writer, sheet_name='answer_count')

        # 상위권, 중위권, 하위권 시트 저장
        for group_name in ['top', 'mid', 'low']:
            combined_group_df = pd.concat(group_choice_counts_all[group_name], ignore_index=True)
            combined_group_df.to_excel(writer, sheet_name=f'answer_count_{group_name}')

    print(f"✅ '{output_excel}' 파일에 모든 시트를 저장했습니다.")


def generate_student_answers(df, num_students):
    probs_matrix = df[['①', '②', '③', '④', '⑤']].div(df[['①', '②', '③', '④', '⑤']].sum(axis=1), axis=0)
    # 각 문제마다 num_students 명의 선택지를 생성
    response_array = np.array([
        np.random.choice([1, 2, 3, 4, 5], size=num_students, p=probs_matrix.iloc[q_idx].values)
        for q_idx in range(len(df))
    ]).T  # 전치하여 (num_students, num_questions) 형태로 만듦
    return response_array


def compute_scores(correct_answers, response_array, exam, subject):
    score_array = (response_array == np.array(correct_answers)).sum(axis=1)
    raw_score_array = np.round(score_array / len(correct_answers) * 100, 1)
    base_mean = STANDARD_BASE_MEANS[exam].get(subject, 50)
    base_std = STANDARD_BASE_STDS[exam].get(subject, 10)
    std_score_array = np.round(
        (score_array - score_array.mean()) / score_array.std() * base_std + base_mean, 1)
    return score_array, raw_score_array, std_score_array


def get_descending_ranks(values: np.ndarray) -> np.ndarray:
    # 동점자에게 동일한 등수 부여
    sorted_idx = np.argsort(-values)
    sorted_values = values[sorted_idx]
    ranks = np.empty_like(values, dtype=int)

    current_rank = 1
    for i in range(len(values)):
        if i > 0 and sorted_values[i] != sorted_values[i - 1]:
            current_rank = i + 1
        ranks[sorted_idx[i]] = current_rank
    return ranks


def compute_statistics(values):
    return {
        'max': values.max(),
        't10': np.percentile(values, 90),
        't25': np.percentile(values, 75),
        't50': np.percentile(values, 50),
        'min': values.min(),
        'avg': values.mean(),
        'std': values.std(),
    }


def generate_frequency_table(values: np.ndarray, subject: str, bin_width: int = 10) -> pd.DataFrame:
    """구간 기반 도수분포표 생성 함수

    Args:
        values (np.ndarray): 학생 점수 데이터
        subject (str): 과목 필드 (혹은 'total')
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
    if bin_width == 1:
        labels = [b for b in bins[:-1]]
    else:
        labels = [f'{b}점 이상~{b + bin_width}점 미만' for b in bins[:-1]]

    binned = pd.cut(series, bins=bins, labels=labels, right=False)
    freq = binned.value_counts().sort_index()
    freq_df = freq.rename_axis('bin').reset_index(name='frequency')
    freq_df.insert(0, 'subject', subject)

    return freq_df


def create_groupwise_answer_counts_by_rank(response_array: np.ndarray, ranks: np.ndarray) -> dict:
    """등수 기반 그룹별 보기 선택 개수 반환

    Args:
        response_array (np.ndarray): (학생 수, 문항 수)
        ranks (np.ndarray): 1등부터 N등까지의 등수 배열

    Returns:
        dict[str, pd.DataFrame]: 그룹 이름 → 선택 수 DataFrame
    """
    num_students = len(ranks)
    top_threshold = int(num_students * 0.27)  # 상위 27%
    bottom_threshold = num_students - top_threshold  # 하위 27%

    sorted_idx = np.argsort(ranks)  # 낮은 등수가 먼저

    group_indices = {
        'all': np.arange(num_students),
        'top': sorted_idx[:top_threshold],
        'mid': sorted_idx[top_threshold:bottom_threshold],
        'low': sorted_idx[bottom_threshold:],
    }

    result = {}
    for label, indices in group_indices.items():
        group_response = response_array[indices]
        df = calculate_answer_distribution(group_response)
        result[label] = df

    return result


def calculate_answer_distribution(response_array: np.ndarray) -> pd.DataFrame:
    """문항별 학생 선택률(①~⑤)을 계산하여 DataFrame으로 반환

    Args:
        response_array (np.ndarray): (학생 수, 문항 수) 형태의 배열

    Returns:
        pd.DataFrame: 각 문항별 선택률 (1~5번 보기 기준)
    """
    num_questions = response_array.shape[1]
    result = []

    for idx in range(num_questions):
        choices = response_array[:, idx]
        counts = pd.Series(choices).value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
        total = counts.sum()
        row = counts.round(4).values.tolist() + [total]
        result.append(row)

    return pd.DataFrame(
        result,
        columns=['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum'],
        index=[i + 1 for i in range(num_questions)],
    )
