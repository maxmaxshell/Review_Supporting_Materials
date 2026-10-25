import argparse

import csv

import hashlib

import html

import json

import os

import re

import sqlite3

import time

import urllib.error

import urllib.parse

import urllib.request

from pathlib import Path

START_DATE = '2015-01-01'

END_DATE = '2026-06-30'

LANGUAGE = 'en'

DOCUMENT_TYPES = ('article', 'review')

def normalize_doi(value):
    return re.sub('^(?:https?://(?:dx\\.)?doi\\.org/|doi\\s*:\\s*)', '', str(value or '').strip(), flags=re.I).lower()

def abstract_text(value):
    if not value:
        return ''
    positions = {}
    for (word, indexes) in value.items():
        for index in indexes:
            if index in positions and positions[index] != word:
                raise ValueError('Conflicting abstract positions')
            positions[index] = word
    return ' '.join((positions[index] for index in sorted(positions)))

def text_value(value):
    if isinstance(value, str):
        return html.unescape(re.sub('<[^>]+>', ' ', value)).strip()
    if isinstance(value, list):
        return ' '.join(filter(None, (text_value(item) for item in value)))
    if isinstance(value, dict):
        return text_value(value.get('$', value.get('para', '')))
    return ''

def keyword_values(value):
    if isinstance(value, str):
        return [item.strip() for item in value.split(';') if item.strip()]
    if isinstance(value, dict):
        return keyword_values(value.get('author-keyword', value.get('authkeywords', value.get('$', ''))))
    if isinstance(value, list):
        return [text for item in value if (text := text_value(item))]
    return []

def normalize_openalex(work):
    source = (work.get('primary_location') or {}).get('source') or {}
    return {'openalex_id': work['id'], 'doi': normalize_doi(work.get('doi')), 'title': work.get('title') or work.get('display_name') or '', 'abstract': abstract_text(work.get('abstract_inverted_index')), 'keyword_channels': {'openalex_model_keywords': [item['display_name'] for item in work.get('keywords') or [] if item.get('display_name')]}, 'publication_date': work.get('publication_date'), 'publication_year': work.get('publication_year'), 'language': work.get('language'), 'openalex_type': work.get('type'), 'journal': source.get('display_name', ''), 'journal_id': source.get('id', ''), 'authorship_count': len(work.get('authorships') or []), 'is_retracted': bool(work.get('is_retracted')), 'is_paratext': bool(work.get('is_paratext'))}

class Client:

    def __init__(self, config):
        self.config = config
        self.previous = {}
        self.disabled = set()
        self.indices = {}

    def request(self, provider, url, params=None, headers=None):
        if provider in self.disabled:
            return None
        options = self.config.get('providers', {}).get(provider, {})
        accounts = [item for item in options.get('accounts', []) if item.get('enabled', True) and item.get('api_key')]
        index = self.indices.get(provider, 0)
        for attempt in range(5):
            if accounts and index >= len(accounts):
                self.disabled.add(provider)
                return None
            key = accounts[index]['api_key'] if accounts else ''
            query = dict(params or {})
            request_headers = {'Accept': 'application/json', 'User-Agent': 'BibliometricResearch/1.0', **(headers or {})}
            if key:
                if provider in ('openalex', 'springer_nature'):
                    query['api_key'] = key
                else:
                    request_headers['x-api-key' if provider == 'semantic_scholar' else 'X-ELS-APIKey'] = key
            gap = max(1.1 if provider == 'semantic_scholar' else 0.2, float(options.get('minimum_interval_seconds', 0)))
            time.sleep(max(0, gap - (time.monotonic() - self.previous.get(provider, -gap))))
            self.previous[provider] = time.monotonic()
            target = url + ('?' + urllib.parse.urlencode(query) if query else '')
            try:
                with urllib.request.urlopen(urllib.request.Request(target, headers=request_headers), timeout=60) as response:
                    return json.load(response)
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    return None
                if error.code == 401 and accounts:
                    index += 1
                    self.indices[provider] = index
                    continue
                if error.code == 403:
                    self.disabled.add(provider)
                    return None
                if error.code == 429:
                    self.disabled.add(provider)
                    return None
                if error.code >= 500:
                    time.sleep(min(30, 2 ** attempt))
                    continue
                raise RuntimeError('Provider request rejected with HTTP ' + str(error.code)) from None
            except (urllib.error.URLError, TimeoutError):
                time.sleep(min(30, 2 ** attempt))
        raise RuntimeError('Provider request retry limit reached')

def provider_metadata(client, provider, doi):
    quoted = urllib.parse.quote(doi, safe='')
    if provider == 'semantic_scholar':
        data = client.request(provider, 'https://api.semanticscholar.org/graph/v1/paper/DOI:' + quoted, {'fields': 'title,abstract,externalIds,publicationTypes'})
        if data and normalize_doi((data.get('externalIds') or {}).get('DOI')) == doi:
            return {'doi': doi, 'title': data.get('title') or '', 'abstract': data.get('abstract') or '', 'keywords': [], 'document_type': data.get('publicationTypes') or []}
    elif provider == 'elsevier':
        data = client.request(provider, 'https://api.elsevier.com/content/abstract/doi/' + quoted, {'view': 'FULL'})
        if data:
            response = data.get('abstracts-retrieval-response') or {}
            core = response.get('coredata') or {}
            if normalize_doi(core.get('prism:doi')) == doi:
                return {'doi': doi, 'title': text_value(core.get('dc:title')), 'abstract': text_value(core.get('dc:description')), 'keywords': keyword_values(response.get('authkeywords')), 'document_type': core.get('subtypeDescription', '')}
    elif provider == 'springer_nature':
        data = client.request(provider, 'https://api.springernature.com/meta/v2/json', {'q': 'doi:' + doi, 'p': 10})
        if data:
            matches = [item for item in data.get('records', []) if normalize_doi(item.get('doi')) == doi]
            if len(matches) == 1:
                record = matches[0]
                return {'doi': doi, 'title': record.get('title') or '', 'abstract': text_value(record.get('abstract')), 'keywords': keyword_values(record.get('keyword') or record.get('keywords')), 'document_type': record.get('contentType', '')}
    return None
