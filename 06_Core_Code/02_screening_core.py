import argparse

import csv

import hashlib

import json

import re

import unicodedata

from collections import defaultdict

from difflib import SequenceMatcher

from pathlib import Path

RULES = [{'type': 'original_research', 'score': 12, 'minimum_words': 35, 'require': {'abstract': '(?s)(?=.*\\b(?:we\\s+(?:measured|tested|fabricated|collected|derive|prove)|(?:was|were)\\s+(?:studied|tested|measured|fabricated)|(?:system|equations?|problem)\\b[^.!?]{0,65}\\b(?:solved|formulated)|(?:proposed|developed)\\s+(?:method|model|algorithm|formulation|methodology))\\b)(?=.*\\b(?:(?:results?|data|experiments?)\\b[^.!?]{0,75}\\b(?:show|reveal|demonstrat|indicat)\\w*|it is (?:shown|revealed)|validated|verified)\\b)'}, 'block': {'title': '\\b(?:review|survey|bibliometric|scientometric|meta.analysis|literature)\\b', 'abstract': '\\b(?:review|survey|bibliometric|scientometric|meta.analysis|literature)\\b'}, 'settles_source': False, 'settles_history': False, 'id': 'R001'}, {'type': 'exclude_nonresearch', 'score': 13, 'minimum_words': 0, 'authors_required': False, 'require': {'title': '^\\s*(?:\\[?(?:front|back)\\s+cover\\]?\\s*$|(?:guest\\s+)?editorial\\s*(?::|$)|(?:correction|corrigendum|erratum|retraction|retracted|withdrawn|notice of removal|removed)\\s*(?::|\\bto\\b)|acknowledg(?:e)?ment(?:s)?\\s+to\\s+(?:the\\s+)?reviewers|announc(?:ing|ement)\\b[^.!?]{0,120}\\b(?:awards?|prizes?|competition)|call\\s+for\\s+papers\\b)|\\beditor[\\u2019\\x27]s\\s+comment\\s*$'}, 'id': 'R002'}, {'type': 'original_research', 'score': 12, 'minimum_words': 45, 'require': {'abstract': '(?s)(?=.*(?:\\b(?:equations?|eigenmodes?|eigenvalues?|mathematical model|boundary.value problem|finite.element|numerical (?:model|simulation|analysis)|density.functional|first.principles|DFT)\\b))(?=.*(?:\\b(?:are|is|were|was|have been|has been)\\s+(?:(?:numerically|analytically|successfully)\\s+)?(?:computed|solved|discreti[sz]ed|derived|formulated|conducted|implemented|developed|analy[sz]ed)\\b))(?=.*(?:\\b(?:it is shown|is shown to|results?\\b[^.!?]{0,80}\\b(?:show|indicat|reveal|demonstrat)\\w*|(?:insights|relations?|responses?|solutions?)\\b[^.!?]{0,80}\\b(?:obtained|established)|(?:simulations?|calculations?)\\b[^.!?]{0,80}\\b(?:demonstrat|indicat|reveal|show)\\w*)\\b))'}, 'block': {'title': '\\b(?:review|survey|bibliometric|scientometric|meta.analysis|literature)\\b|\\b(?:previous|published|existing|earlier|prior)\\s+(?:studies|papers|research|reports)\\b', 'abstract': '\\b(?:review|survey|bibliometric|scientometric|meta.analysis|literature)\\b|\\b(?:previous|published|existing|earlier|prior)\\s+(?:studies|papers|research|reports)\\b'}, 'settles_source_when_external_agrees': True, 'id': 'R003'}, {'type': 'review', 'score': 12, 'minimum_words': 35, 'require': {'abstract': '\\b(?:(?:this|the present|the current|the)\\s+(?:paper|article|study|work)\\s*(?:,?\\s*(?:therefore|thus|also)\\s*,?\\s*)?(?:(?:aims?|attempts?|seeks?)\\s+to\\s+)?(?:(?:systematically|critically|comprehensively|thoroughly)\\s+)?(?:(?:provides?|offers?|gives?|presents?)\\s+(?:(?:an?|the)\\s+)?(?:(?:systematic|comprehensive|critical|detailed|literature|state.of.the.art)\\s+){0,3}(?:review|overview\\s+of\\s+(?:(?:the\\s+)?(?:literature|existing|current|published|previous)\\b))\\b|review(?:s|ed)?\\s+(?:contemporary|recent|existing|previous|the current)\\s+(?:research|studies|methods|advances))|(?:in this (?:paper|work)|here)\\s*,?\\s*we\\s+(?:will\\s+)?(?:provide|present|offer|give)\\s+(?:an?|the)\\s+(?:(?:systematic|comprehensive|critical|detailed|literature)\\s+){0,3}review\\b|in this\\s+research\\s+review\\b|we\\s+review(?:ed)?\\s+the\\s+(?:most important|major|main)\\s+(?:achievements|advances|developments)\\b)'}, 'block': {'abstract': '\\b(?:primary|main)\\s+(?:aim|objective|purpose|contribution)\\b[^.!?]{0,100}\\b(?:propose|develop|design|derive|experiment|measure|test)\\w*|\\b(?:then|subsequently|following (?:this|the) review|after (?:this|the) review)\\b[^.!?]{0,100}\\bwe\\b[^.!?]{0,70}\\b(?:propos|develop|design|experiment|collect)\\w*'}, 'settles_source': True, 'settles_history': True, 'id': 'R004'}, {'type': 'original_research', 'score': 12, 'minimum_words': 45, 'require': {'abstract': '(?s)(?=.*(?:\\b(?:were|was|are|is|have been|has been)\\s+(?:(?:then|subsequently|sequentially|successfully|experimentally|directly)\\s+){0,2}(?:inoculated|manufactured|prepared|fabricated|strengthened|instrumented|captured|recorded|monitored|examined|characteri[sz]ed|compared|evaluated|conducted|performed|measured|tested|implemented|incorporated)\\b|\\b(?:this|our|the present)\\s+(?:study|work|investigation)\\b[^.!?]{0,120}\\b(?:experimental|field|laboratory|monitoring|employed|tested|measured)\\b))(?=.*(?:\\b(?:results?|data|tests?|measurements?|outcomes|experiments?)\\b[^.!?]{0,80}\\b(?:show|indicat|reveal|demonstrat|confirm|found|correlat)\\w*|\\bwere found to\\b|\\b(?:removal efficiency|(?:ultimate\\s+)?(?:bearing|adsorption|load.carrying) capacit(?:y|ies)|strength|modulus|stiffness|distribution)\\b[^.!?]{0,90}(?:\\d+(?:\\.\\d+)?\\s*%|increas\\w*|decreas\\w*|compar\\w*)))(?=.*(?:\\b(?:specimens?|samples?|concrete|composites?|fib(?:er|re)s?|nanoparticles?|water|bacteria|electrodes?|strain|beams?|CMOS|laser|Sporosarcina|physical|laboratory|microscope|tensile|soil|structures?|bridges?)\\b))'}, 'block': {'title': '\\b(?:review|survey|bibliometric|scientometric|meta.analysis|literature)\\b|\\b(?:previous|published|existing|earlier|prior)\\s+(?:studies|papers|research|reports)\\b', 'abstract': '\\b(?:review|survey|bibliometric|scientometric|meta.analysis|literature)\\b|\\b(?:previous|published|existing|earlier|prior)\\s+(?:studies|papers|research|reports)\\b|\\b(?:publications?|papers|literature|peer.reviewed|published\\s+(?:studies|reports|data)|data\\s+(?:extracted|compiled|collected|obtained|derived)\\s+from|data\\s+from\\s+(?:more than\\s+|over\\s+|about\\s+)?\\d+\\s+(?:studies|articles))\\b'}, 'settles_source_when_external_agrees': True, 'id': 'R005'}, {'type': 'review', 'score': 12, 'minimum_words': 20, 'require': {'abstract': '\\b(?:this|the present|the current)\\s+(?:paper|article|study|work)\\s+(?:(?:aims?|seeks?|attempts?)\\s+to\\s+)?(?:provide[sd]?|present[sd]?|offer[sd]?|give[sn]?)\\s+(?:an?|the)\\s+(?:(?:targeted|focused|systematic|comprehensive|critical|state.of.the.art)\\s+){0,3}review\\b|(?:^|[.!?]\\s+)(?:Abstract\\s+)?(?:In\\s+this\\s+(?:(?:systematic|comprehensive|critical|literature)\\s+){0,2}review\\b|This\\s+(?:(?:systematic|comprehensive|critical|literature)\\s+){0,2}review\\s+(?:systematically\\s+|critically\\s+)?(?:describes?|focuses?|discusses?|summari[sz]es?|analy[sz]es?|examines?|covers?|classifies?|evaluates?|presents?|provides?)\\b)'}, 'block': {'abstract': '\\b(?:primary|main)\\s+(?:aim|objective|purpose|contribution)\\b[^.!?]{0,100}\\b(?:propose|develop|design|derive|experiment|measure|test)\\w*|\\b(?:then|subsequently|following (?:this|the) review|after (?:this|the) review)\\b[^.!?]{0,100}\\bwe\\b[^.!?]{0,70}\\b(?:propos|develop|design|experiment|collect)\\w*'}, 'settles_source': True, 'settles_history': True, 'id': 'R006'}, {'type': 'exclude_nonresearch', 'score': 17, 'minimum_words': 0, 'authors_required': False, 'any_field_patterns': [{'title': '(?:(?:^|[.!?:]\\s+)(?:comments?\\s+on\\s*:\\s*|comments?\\s+on\\s+[\\u201c\\x22\\x27]|comments?\\s+on\\s+[^.!?]{0,90}\\bet\\s+al\\b|reply\\s+to\\s+(?:the\\s+)?comments?\\b|response\\s+to\\s+comments?\\b))|(?:^\\s*(?:\\[?(?:front|back)\\s+cover\\]?\\s*$|(?:guest\\s+)?editorial\\s*(?::|$)|(?:correction|corrigendum|erratum|retraction|retracted|withdrawn|notice of removal|removed)\\s*(?::|\\bto\\b)|acknowledg(?:e)?ment(?:s)?\\s+to\\s+(?:the\\s+)?reviewers|announc(?:ing|ement)\\b[^.!?]{0,120}\\b(?:awards?|prizes?|competition)|call\\s+for\\s+papers\\b)|\\beditor[\\u2019\\x27]s\\s+comment\\s*$)', 'abstract': '^\\s*(?:abstract\\s+)?(?:this\\s+Forum\\s+article\\s+presents\\s+(?:an?\\s+)?(?:argument|view|opinion)|OPINION\\s+article\\b|(?:Guest\\s+)?Editorial\\s+(?:article|Front\\.))|^\\s*(?:abstract\\s+)?Welcome\\s+to\\s+the\\s+(?:section|Special\\s+Issue)\\b'}], 'verify_opinion_header_doi': True, 'id': 'R007'}]

def normalize(value):
    return ' '.join(re.findall('[^\\W_]+', unicodedata.normalize('NFKC', str(value or '')).casefold()))

def normalize_doi(value):
    return re.sub('^(?:https?://(?:dx\\.)?doi\\.org/|doi\\s*:\\s*)', '', str(value or '').strip(), flags=re.I).lower()

def nonempty_keywords(record):
    channels = record.get('keyword_channels') or {}
    return any((bool(values) for values in channels.values())) or bool(record.get('keywords'))

def pattern_hit(pattern, text):
    operation = re.match if pattern.startswith('(?s)(?=') else re.search
    return bool(operation(pattern, text, re.I))

def match_rules(record):
    fields = {'title': record.get('title') or '', 'abstract': record.get('abstract') or ''}
    words = len(fields['abstract'].split())
    proposals = []
    for rule in RULES:
        if not rule.get('minimum_words', 0) <= words <= rule.get('maximum_words', 10000000):
            continue
        if rule.get('authors_required', True) and (not record.get('authorship_count')):
            continue
        if rule.get('authors_zero') and record.get('authorship_count'):
            continue
        if any((not pattern_hit(pattern, fields[field]) for (field, pattern) in rule.get('require', {}).items())):
            continue
        if any((pattern_hit(pattern, fields[field]) for (field, pattern) in rule.get('block', {}).items())):
            continue
        if any((not any((pattern_hit(pattern, fields[field]) for (field, pattern) in alternatives.items())) for alternatives in rule.get('any_field_patterns', []))):
            continue
        if rule.get('verify_opinion_header_doi') and re.match('^\\s*OPINION\\s+article\\b', fields['abstract'], re.I):
            found = re.search('10\\.\\d{4,9}/[^\\s<>]+', fields['abstract'], re.I)
            if found and normalize_doi(found.group().rstrip('.,;')) != normalize_doi(record.get('doi')):
                continue
        proposals.append({'rule': rule['id'], 'type': rule['type'], 'score': rule.get('score', 12)})
    return proposals

def classify(record):
    if not str(record.get('title') or '').strip() or not normalize_doi(record.get('doi')):
        return ('excluded', 'missing_title_or_doi', [])
    if not str(record.get('abstract') or '').strip():
        return ('excluded', 'missing_abstract_reversible_assumption', [])
    if not nonempty_keywords(record):
        return ('pending', 'missing_keywords', [])
    proposals = match_rules(record)
    if re.search('^Aeroacoustics research in Europe\\s*:\\s*The CEAS[-\\u2013]ASC report on\\s+\\d{4}\\s+highlights', record['title'], re.I):
        return ('excluded', 'society_annual_highlights_policy', proposals)
    scores = {}
    for proposal in proposals:
        scores[proposal['type']] = max(scores.get(proposal['type'], 0), proposal['score'])
    if not scores:
        return ('pending', 'insufficient_content_evidence', proposals)
    ranked = sorted(scores, key=scores.get, reverse=True)
    margin = scores[ranked[0]] - (scores[ranked[1]] if len(ranked) > 1 else 0)
    if margin < 3 or scores[ranked[0]] < 9:
        return ('pending', 'conflicting_content_rules', proposals)
    if ranked[0] == 'exclude_nonresearch':
        return ('excluded', 'explicit_nonresearch_form', proposals)
    body = record['abstract']
    if record.get('is_retracted') or record.get('is_paratext') or normalize(body) == normalize(record['title']):
        return ('pending', 'integrity_or_metadata_quality', proposals)
    if re.match('^\\s*ISSN\\s*:\\s*[\\dXx-]+\\s*$', body) or re.search('^\\d{6}\\s+[a-z]{2,8}\\b|;\\s*(?:Published|Others|Green\\s*\\(AAM\\))\\s*;', body, re.I):
        return ('pending', 'suspect_abstract_metadata', proposals)
    if len(body.split()) < 120 and re.search('^\\s*(?:Presidential\\s+Graduate\\s+Fellowship|Sponsorship\\s*:|Funding\\s*:|Acknowledg(?:e)?ments\\s*:|The authors would like to express gratitude)', body, re.I):
        return ('pending', 'funding_as_abstract', proposals)
    previous = record.get('prior_decisions') or []
    positive = [value for value in previous + [ranked[0]] if value in ('original_research', 'review')]
    if sum((left != right for (left, right) in zip(positive, positive[1:]))) >= 2:
        return ('pending', 'historical_type_reversals', proposals)
    if record.get('source_type_conflict') or record.get('clinical_scope_hold') or record.get('review_required'):
        return ('pending', 'unresolved_source_or_scope_conflict', proposals)
    return (ranked[0], 'content_rule_candidate_requires_local_validation', proposals)
