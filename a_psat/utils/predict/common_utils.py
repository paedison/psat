from dataclasses import dataclass

from a_psat import models


@dataclass(kw_only=True)
class ModelData:
    def __post_init__(self):
        self.psat = models.Psat
        self.problem = models.Problem

        self.predict_psat = models.PredictPsat
        self.category = models.PredictCategory
        self.statistics = models.PredictStatistics
        self.student = models.PredictStudent
        self.answer = models.PredictAnswer
        self.score = models.PredictScore

        self.rank_total = models.PredictRankTotal
        self.rank_category = models.PredictRankCategory
        self.rank_model_set = {'total': self.rank_total, 'category': self.rank_category}

        self.ac_all = models.PredictAnswerCount
        self.ac_top = models.PredictAnswerCountTopRank
        self.ac_mid = models.PredictAnswerCountMidRank
        self.ac_low = models.PredictAnswerCountLowRank
        self.ac_model_set = {'all': self.ac_all, 'top': self.ac_top, 'mid': self.ac_mid, 'low': self.ac_low}
