from pathlib import Path
from typing import Hashable

import numpy as np
import pandas as pd
from openpyxl.reader.excel import load_workbook
from openpyxl.utils import get_column_letter

from . import utils


def run():
    exam = utils.get_user_input('시험(0: LEET, 1: PSAT 5급, 2: PSAT 7급): ', 0, int)
    num_students = utils.get_user_input('학생 수: ', 1000, int)
    input_excel_file = utils.get_user_input('답안 선택률 엑셀 파일명: ', '선택률', str)
    output_excel_file = utils.get_user_input('가상 답안 엑셀 파일명: ', '가상_답안', str)

    if exam == 0:
        fake_answer = LeetFakeAnswer(num_students, input_excel_file, output_excel_file)
    elif exam == 1:
        fake_answer = PsatHaengsiFakeAnswer(num_students, input_excel_file, output_excel_file)
    else:
        fake_answer = PsatChilgeubFakeAnswer(num_students, input_excel_file, output_excel_file)

    output_excel = fake_answer.output_excel
    sheet_data = fake_answer.get_sheet_data()
    group_df_set = fake_answer.get_answer_count_group_df_set()

    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        for sheet_name, df in sheet_data.items():
            df.to_excel(writer, sheet_name=sheet_name)

        for sheet_name, df in group_df_set.items():
            fake_answer.change_index_to_subject_number(df)
            df.to_excel(writer, sheet_name=f'answer_count_{sheet_name}')

    fake_answer.adjust_column_widths()
    print(f"✅ '{output_excel}' 파일에 모든 시트를 저장했습니다.")


class LeetFakeAnswer:
    BASE_DIR = Path('D:/projects/#generate_virtual_answers')

    SUBJECTS = ['subject_0', 'subject_1']
    SUBJECTS_PLUS_TOTAL = SUBJECTS + ['total']
    BASE_MEANS = {'subject_0': 45, 'subject_1': 60}
    BASE_STDS = {'subject_0': 10, 'subject_1': 10}

    RANK_LABEL = 'standard_score'
    METRICS = ['correct_count', 'percentage_score', 'standard_score']
    STAT_KEYS = ['max', 't10', 't25', 't50', 'min', 'avg', 'std']
    BIN_WIDTH = 10

    def __init__(self, num_students: int, input_excel_file: str, output_excel_file: str):
        self.num_students = num_students
        self.input_excel = self.get_excel_file(input_excel_file)
        self.output_excel = self.get_excel_file(output_excel_file)

        # 가상 데이터 생성
        self.all_correct_answers = []
        self.all_answers, self.all_scores, self.all_stats, self.temp_totals = {}, {}, {}, {}
        self.update_all_fake_data()

        # 학생 정보
        self.ids = [f'fake{i:04}' for i in range(1, num_students + 1)]
        self.student_df = self.get_student_df()

        # 답안/성적 데이터프레임
        self.answer_df = self.get_answer_df()
        self.score_df = self.get_score_df()
        self.update_score_and_answer_df()

    def get_excel_file(self, filename):
        return self.BASE_DIR / f'{filename}.xlsx'

    def update_all_fake_data(self):
        df = pd.read_excel(self.input_excel, index_col=[0, 1, 2], sheet_name='answer_count')

        for subject in self.SUBJECTS:
            df_subject = df[df.index.get_level_values('field') == subject]
            correct_answers = df_subject['answer'].tolist()
            student_answers = self.generate_student_answers(df_subject)
            correct_counts, percentage_scores, standard_scores = self.compute_scores(
                subject, correct_answers, student_answers)

            self.all_answers[subject] = student_answers
            self.all_scores[subject] = {
                'correct_count': correct_counts,
                'percentage_score': percentage_scores,
                'standard_score': standard_scores,
            }

            self.all_correct_answers.extend([(subject, idx + 1, ans) for idx, ans in enumerate(correct_answers)])
            self.all_stats[subject] = {k: self.compute_statistics(self.all_scores[subject][k]) for k in self.METRICS}

        self.all_stats['total'] = {}
        for metric in self.METRICS:
            total = np.sum([self.all_scores[s][metric] for s in self.SUBJECTS], axis=0)
            self.temp_totals[metric] = total
            self.all_stats['total'][metric] = self.compute_statistics(total)
    #
    # def update_all_fake_data(self):
    #     for subject in self.SUBJECTS:
    #         df = pd.read_excel(self.input_excel, sheet_name=subject)
    #         correct_answers = df['answer'].tolist()
    #         student_answers = self.generate_student_answers(df)
    #         correct_counts, percentage_scores, standard_scores = self.compute_scores(
    #             subject, correct_answers, student_answers)
    #
    #         self.all_answers[subject] = student_answers
    #         self.all_scores[subject] = {
    #             'correct_count': correct_counts,
    #             'percentage_score': percentage_scores,
    #             'standard_score': standard_scores,
    #         }
    #
    #         self.all_correct_answers.extend([(subject, idx + 1, ans) for idx, ans in enumerate(correct_answers)])
    #         self.all_stats[subject] = {k: self.compute_statistics(self.all_scores[subject][k]) for k in self.METRICS}
    #
    #     self.all_stats['total'] = {}
    #     for metric in self.METRICS:
    #         total = np.sum([self.all_scores[s][metric] for s in self.SUBJECTS], axis=0)
    #         self.temp_totals[metric] = total
    #         self.all_stats['total'][metric] = self.compute_statistics(total)

    def generate_student_answers(self, df: pd.DataFrame) -> np.array:
        probs_matrix = df[['count_1', 'count_2', 'count_3', 'count_4', 'count_5']].div(
            df[['count_1', 'count_2', 'count_3', 'count_4', 'count_5']].sum(axis=1), axis=0)
        # 각 문제마다 num_students 명의 선택지를 생성
        student_answers = np.array([
            np.random.choice([1, 2, 3, 4, 5], size=self.num_students, p=probs_matrix.iloc[q_idx].values)
            for q_idx in range(len(df))
        ]).T  # 전치하여 (num_students, num_questions) 형태로 만듦

        return student_answers

    def compute_scores(
            self, subject: str, correct_answers: list, student_answers: np.array
    ) -> tuple[np.array, np.array, np.array]:
        correct_counts = (student_answers == np.array(correct_answers)).sum(axis=1)
        percentage_scores = np.round(correct_counts / len(correct_answers) * 100, 1)
        base_mean = self.BASE_MEANS.get(subject, 50)
        base_std = self.BASE_STDS.get(subject, 10)
        standard_scores = np.round(
            (correct_counts - correct_counts.mean()) / correct_counts.std() * base_std + base_mean, 1)

        return correct_counts, percentage_scores, standard_scores

    def get_student_df(self):
        passwords = [f'{np.random.randint(0, 10000):04}' for _ in range(self.num_students)]

        df = pd.read_excel(self.input_excel, sheet_name='aspiration')
        universities = df['university'].tolist()

        for i in range(1, 3):
            aspiration_col = f'aspiration_{i}'
            rate_col = f'rate_{i}'
            df[rate_col] = df[aspiration_col] / df[aspiration_col].sum()

        aspiration_1 = np.random.choice(universities, size=self.num_students, p=df['rate_1'].tolist())
        aspiration_2 = []
        for fc in aspiration_1:
            available_univs = [u for u in universities if u != fc]
            available_probs = [df.loc[df['university'] == u, 'rate_2'].values[0] for u in available_univs]
            total = sum(available_probs)
            norm_probs = [p / total for p in available_probs]
            aspiration_2.append(np.random.choice(available_univs, p=norm_probs))

        student_data = {
            'password': passwords,
            'aspiration_1': aspiration_1,
            'aspiration_2': aspiration_2,
        }
        return pd.DataFrame(student_data, index=self.ids)

    def get_answer_df(self) -> pd.DataFrame:
        answer_cols = pd.MultiIndex.from_tuples([
            (s, i + 1) for s in self.SUBJECTS for i in range(self.all_answers[s].shape[1])
        ])
        answers_combined = np.hstack([self.all_answers[s] for s in self.SUBJECTS])
        answer_df = pd.DataFrame(answers_combined, index=self.ids, columns=answer_cols)
        answer_df.index.name = 'serial'
        return answer_df

    def get_score_df(self) -> pd.DataFrame:
        score_data = {}
        for metric in self.METRICS:
            for subject in self.SUBJECTS:
                score_data[(metric, subject)] = self.all_scores[subject][metric]
            score_data[(metric, 'total')] = self.temp_totals[metric]

            # 등수 계산 및 score_data에 추가
            for subject in self.SUBJECTS_PLUS_TOTAL:
                if subject == 'total':
                    values = self.temp_totals[self.RANK_LABEL]
                else:
                    values = self.all_scores[subject][self.RANK_LABEL]
                score_data[('rank', subject)] = self.get_descending_ranks(values)

        score_df = pd.DataFrame(score_data, index=self.student_df.index)
        student_df = pd.DataFrame(self.student_df)
        student_df.columns = pd.MultiIndex.from_tuples([
            ('student', 'password'), ('student', 'aspiration_1'), ('student', 'aspiration_2')
        ])
        score_df = student_df.join(score_df, how='left')

        return score_df

    def update_score_and_answer_df(self):
        for subject in reversed(self.SUBJECTS_PLUS_TOTAL):
            rank_subject_label = (self.RANK_LABEL, subject)
            quantiles = self.score_df[rank_subject_label].quantile([0.27, 0.73])

            def classify_group(score):
                if score <= quantiles[0.27]:
                    return 'low'
                elif score <= quantiles[0.73]:
                    return "mid"
                else:
                    return 'top'

            group_label = ('group', subject)
            group_col = self.score_df[rank_subject_label].apply(classify_group)
            self.score_df.insert(3, group_label, group_col)
            self.answer_df.insert(0, group_label, group_col)

    def get_sheet_data(self):
        return {
            'correct_answer': self.get_correct_answer_df(),
            'score': self.score_df,
            'answer': self.answer_df,
            'aspiration': self.get_aspiration_df(),
            'statistics': self.get_stat_df(),
            'frequency': self.get_freq_df(),
            'answer_count': self.get_answer_count_df(),
        }

    def get_correct_answer_df(self) -> pd.DataFrame:
        correct_answer_df = pd.DataFrame(self.all_correct_answers, columns=['subject', 'number', 'answer'])
        subject = correct_answer_df.pop('subject')
        number = correct_answer_df.pop('number')
        correct_answer_df.index = pd.MultiIndex.from_arrays([subject, number])
        return correct_answer_df

    def get_aspiration_df(self) -> pd.DataFrame:
        aspiration_1_counts = self.student_df['aspiration_1'].value_counts().sort_index()
        aspiration_2_counts = self.student_df['aspiration_2'].value_counts().sort_index()
        aspiration_total_counts = aspiration_1_counts.add(aspiration_2_counts, fill_value=0)

        aspiration_df = pd.DataFrame({
            'aspiration_1': aspiration_1_counts,
            'aspiration_2': aspiration_2_counts,
            'total': aspiration_total_counts,
        }).fillna(0).astype(int)
        aspiration_df.index.name = 'university'

        aspiration_df = aspiration_df.reset_index()
        aspiration_df['sort_key'] = aspiration_df['university'].apply(lambda x: 'ㅎㅎㅎ' if x == '기타 대학' else x)
        aspiration_df = aspiration_df.sort_values('sort_key').drop(columns='sort_key')
        aspiration_df = aspiration_df.set_index('university')

        return aspiration_df

    def get_stat_df(self) -> pd.DataFrame:
        stat_rows = [
            ((m, s), [round(self.all_stats[s][m].get(k, 0), 1) for k in self.STAT_KEYS])
            for m in self.METRICS for s in self.SUBJECTS_PLUS_TOTAL
        ]
        stat_index = pd.MultiIndex.from_tuples([row[0] for row in stat_rows], names=['metric', 'subject'])
        return pd.DataFrame([row[1] for row in stat_rows], index=stat_index, columns=self.STAT_KEYS)

    def get_freq_df(self) -> pd.DataFrame:
        freq_rows = []
        for metric in self.METRICS:
            for subject in self.SUBJECTS_PLUS_TOTAL:
                if subject == 'total':
                    values = self.temp_totals[metric]
                else:
                    values = self.all_scores[subject][metric]

                bin_width = 1 if metric == 'correct_count' else self.BIN_WIDTH
                freq_df = self.generate_frequency_table(values, subject, bin_width)

                for _, row in freq_df.iterrows():
                    freq_rows.append((metric, row['subject'], row['bin'], row['frequency']))

        freq_df = pd.DataFrame(freq_rows, columns=['metric', 'subject', 'bin', 'freq'])
        freq_df.set_index(['metric', 'subject', 'bin'], inplace=True)

        return freq_df

    def get_answer_count_df(self) -> pd.DataFrame:
        choice_counts = []
        for subject in self.SUBJECTS:
            response_array = self.all_answers[subject]
            answer_distribution = self.calculate_answer_distribution(response_array, subject)
            choice_counts.append(answer_distribution.reset_index(drop=True))

        answer_count_df = pd.concat(choice_counts, ignore_index=True)
        self.change_index_to_subject_number(answer_count_df)

        return answer_count_df

    def get_answer_count_group_df_set(self) -> dict[Hashable, pd.DataFrame]:
        group_df_set = {}
        answer_cols = [col for col in self.answer_df.columns if col[0] != 'group']
        student_groups = self.answer_df.groupby(('group', 'total'))

        for group_name, group_df in student_groups:
            count_data = []

            for subject in self.SUBJECTS:
                subject_cols = [col for col in answer_cols if col[0] == subject]
                group_subject_df = group_df[subject_cols]

                for number in sorted({col[1] for col in subject_cols}):
                    col = (subject, number)
                    value_counts = group_subject_df[col].value_counts().sort_index()
                    counts = [value_counts.get(i, 0) for i in range(1, 6)]
                    count_sum = sum(counts)
                    count_data.append([subject, number] + counts + [count_sum])

            answer_count_df = pd.DataFrame(count_data, columns=[
                'subject', 'number',
                'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
                'count_sum'
            ])
            group_df_set[group_name] = answer_count_df

        return group_df_set

    def adjust_column_widths(self):
        wb = load_workbook(self.output_excel)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for col_idx, col in enumerate(ws.iter_cols(), 1):
                max_length = 0
                for cell in col:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = max_length + 2
        wb.save(self.output_excel)

    @staticmethod
    def compute_statistics(values: np.array) -> dict[str, int | float]:
        return {
            'max': values.max(),
            't10': np.percentile(values, 90),
            't25': np.percentile(values, 75),
            't50': np.percentile(values, 50),
            'min': values.min(),
            'avg': values.mean(),
            'std': values.std(),
        }

    @staticmethod
    def generate_frequency_table(values: np.ndarray, subject: str, bin_width: int) -> pd.DataFrame:
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

    @staticmethod
    def change_index_to_subject_number(df: pd.DataFrame) -> None:
        subject = df.pop('subject')
        number = df.pop('number')
        df.index = pd.MultiIndex.from_arrays([subject, number])

    @staticmethod
    def calculate_answer_distribution(response_array: np.ndarray, subject: str) -> pd.DataFrame:
        """문항별 학생 선택률(①~⑤)을 계산하여 DataFrame으로 반환

        Args:
            response_array (np.ndarray): (학생 수, 문항 수) 형태의 배열
            subject: 과목 코드

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

        answer_count_df = pd.DataFrame(
            result,
            columns=['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum'],
            index=[i + 1 for i in range(num_questions)],
        )
        answer_count_df.insert(0, 'subject', subject)
        answer_count_df.insert(1, 'number', answer_count_df.index)

        return answer_count_df

    @staticmethod
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


class PsatHaengsiFakeAnswer(LeetFakeAnswer):
    SUBJECTS = ['subject_0', 'subject_1', 'subject_2', 'subject_3']
    BASE_MEANS = {'subject_0': 50, 'subject_1': 50, 'subject_2': 50, 'subject_3': 50}
    BASE_STDS = {'subject_0': 10, 'subject_1': 10, 'subject_2': 10, 'subject_3': 10}
    RANK_LABEL = 'percentile_score'

    def get_temp_totals_and_update_all_stats(self) -> dict[str, np.array]:
        self.all_stats['total'] = {}
        temp_totals = {m: np.sum([self.all_scores[s][m] for s in self.SUBJECTS[1:]], axis=0) for m in self.METRICS}
        for metric in self.METRICS:
            self.all_stats['total'][metric] = self.compute_statistics(temp_totals[metric])
        return temp_totals

    def get_student_df(self):
        passwords = [f'{np.random.randint(0, 10000):04}' for _ in range(self.num_students)]

        df = pd.read_excel(self.input_excel, sheet_name='category')
        total_applicants = df['applicants'].sum()
        df['rate'] = df['applicants'] / total_applicants
        categories = df[['unit'], ['department']].tolist()
        probabilities = df['rate'].tolist()
        category_data = np.random.choice(categories, size=self.num_students, p=probabilities)

        student_data = {
            'password': passwords,
            'unit': '',
            'department': '',
        }
        return pd.DataFrame(student_data, index=self.ids)

    def get_sheet_data(self):
        return {
            'correct_answer': self.get_correct_answer_df(),
            'score': self.score_df,
            'answer': self.answer_df,
            'category': self.get_category_df(),
            'statistics': self.get_stat_df(),
            'frequency': self.get_freq_df(),
            'answer_count': self.get_answer_count_df(),
        }

    def get_category_df(self):
        pass


class PsatChilgeubFakeAnswer(PsatHaengsiFakeAnswer):
    SUBJECTS = ['subject_1', 'subject_2', 'subject_3']

    def get_temp_totals_and_update_all_stats(self) -> dict[str, np.array]:
        return super(PsatHaengsiFakeAnswer).get_temp_totals_and_update_all_stats()
