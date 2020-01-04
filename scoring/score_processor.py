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

from collections import defaultdict

# ArticleData is used to validate that all offsets are correctly aligned and
# from the same underlying article. We could load the entire article to check
# against, but no need for the memory and network hit.
class ArticleData(object):
    def __init__(self):
        self.char_dict = {}
        self.article_id = None

    def check_article_id(self, article_id):
        if self.article_id is None:
            self.article_id = article_id
        else:
            assert(self.article_id == article_id)

    def check_offsets(self, offsets):
        for offset in offsets:
            self.consider(offset)

    # assume we don't have access to full article - build a map of indices to
    # chars for every annotation being processed.
    def consider(self, offset):
        anno_range = range(int(offset['start']), int(offset['end']))
        target_text = offset['text']
        anno_map = dict(zip(anno_range, target_text))
        # set intersection operator
        intersection = self.char_dict.viewkeys() & anno_map.viewkeys()
        # verify any overlaps are consistent with prior text
        for k in intersection:
            assert(self.char_dict[k] == anno_map[k])
        self.char_dict.update(anno_map)


class Highlights(object):
    def __init__(self):
        self.flattened = set()

    def merge_offsets(self, offsets):
        for offset in offsets:
            self.consider(offset)

    def consider(self, offset):
        anno_set = set(range(int(offset['start']), int(offset['end'])))
        # set union operator
        self.flattened |= anno_set


# We do not consider case numbers - each topic is flattened.
class HighlightScoreProcessor(object):
    def __init__(self):
        # Used to verify that we aren't accidentally being passed data from
        # different articles.
        self.article_data = ArticleData()
        self.reference_topics = None
        self.score_topics = None

    def set_reference_tuas(self, reference_tuas):
        self.reference_topics = defaultdict(Highlights)
        for tua in reference_tuas.iterator():
            self.article_data.check_article_id(tua.article_id)
            self.article_data.check_offsets(tua.offsets)
            topic_name = tua.topic_name
            ref_highlights = self.reference_topics[topic_name]
            ref_highlights.merge_offsets(tua.offsets)

    def set_highlight_groups(self, hg_to_score):
        self.score_topics = defaultdict(Highlights)
        for hg in hg_to_score.iterator():
            article_id = hg.article_highlight.highlight_task.article_id
            self.article_data.check_article_id(article_id)
            offsets = hg.get_dict_offsets()
            self.article_data.check_offsets(offsets)
            topic_name = hg.topic_name
            score_highlights = self.score_topics[topic_name]
            score_highlights.merge_offsets(offsets)

    def true_positive(self):
        total_chars = 0
        for (score_topic, score_highlights) in self.score_topics.iteritems():
            ref_highlights = self.reference_topics.get(score_topic, None)
            if ref_highlights is not None:
                # set intersection
                matching_indices = ref_highlights.flattened & score_highlights.flattened
                total_chars += len(matching_indices)
        return total_chars

    def false_positive(self):
        total_chars = 0
        for (score_topic, score_highlights) in self.score_topics.iteritems():
            ref_highlights = self.reference_topics.get(score_topic, None)
            if ref_highlights is not None:
                # set intersection
                matching_indices = ref_highlights.flattened & score_highlights.flattened
                total_chars += len(score_highlights.flattened) - len(matching_indices)
            else:
                # All of this topic are false positive
                total_chars += len(score_highlights.flattened)
        return total_chars

    def max_relevant(self):
        total_chars = 0
        # Each topic has a flattened set of character highlight indices. Add
        # up the number of characters highlighted across all reference topics.
        for topic in self.reference_topics.values():
            total_chars += len(topic.flattened)
        return total_chars
