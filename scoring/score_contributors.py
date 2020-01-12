#  Copyright 2019-2020 Thusly, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import logging
logger = logging.getLogger(__name__)

# from django.db.models import Sum
# from django.contrib import messages
from thresher.models import save_message
from thresher.exceptions import InvalidTaskType

from thresher.models import (Contributor, ContributorScore,
                             HighlightScore, QuizScore)

def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def score_contributors(user_id, tua_group):
    tua_type = tua_group.tua_type
    if tua_type == 'HLTR':
        queryset = HighlightScore.objects.all()
        group_by_join = 'article_highlight__contributor'
    elif tua_type == "QUIZ":
        queryset = QuizScore.objects.all()
        group_by_join = 'quiz_taskrun__contributor'
    else:
        raise InvalidTaskType("tua_type must be "
                               "'HLTR' or 'QUIZ' to build query.")

    totals_by_contributor = (queryset
        .filter(tua_group=tua_group)
        .values(group_by_join)
        .annotate(
            true_positive=Sum('true_positive'),
            false_positive=Sum('false_positive'),
            max_relevant=Sum('max_relevant')
        )
    )

    counter = 0
    for totals in totals_by_contributor:
        contributor_id = totals['article_highlight__contributor']
        true_positive = totals['true_positive']
        false_positive = totals['false_positive']
        max_relevant = totals['max_relevant']
        if true_positive + false_positive != 0:
            precision = float(true_positive) / float(true_positive + false_positive)
        else:
            precision = 1.0 if max_relevant == 0 else 0.0
        if max_relevant != 0:
            recall = float(true_positive) / float(max_relevant)
        else:
            recall = 1.0
        if not isclose(precision + recall, 0.0, abs_tol=1e-09):
            f1 = 2.0 * precision * recall / (precision + recall)
        else:
            f1 = 1.0 if max_relevant == 0 else 0.0
        (contrib_score, created) = ContributorScore.objects.update_or_create(
            tua_group=tua_group,
            contributor_id=contributor_id,
            defaults={
                'score': f1
            }
        )
        counter += 1

    message = ("Used '{}' to calculate scores for {} contributors"
               .format(tua_group.name, counter))
    # save_message(user_id, message, messages.SUCCESS)
