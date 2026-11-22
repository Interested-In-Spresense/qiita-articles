#!/usr/bin/env python3
"""Explicit create/update of a Qiita item. Standard library only."""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ARTICLES = {
    'ADXL335_Spresense': {'title': 'ADXL335のSpresense用ドライバを作ってみる！ ～アナログ入力の落とし穴～', 'tags': ['Spresense', 'Arduino', 'ADXL335']},
    'SubCore_SPI_Spresense': {'title': 'SpresenseのSubCoreからSPIを使ってみる！', 'tags': ['Spresense', 'Arduino', 'SPI']},
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--article', choices=ARTICLES, required=True)
    p.add_argument('--operation', choices=['create', 'update'], required=True)
    p.add_argument('--item-id', default='')
    args = p.parse_args()
    if args.operation == 'update' and not args.item_id.strip():
        p.error('update requires --item-id (Qiita item ID)')
    if args.operation == 'create' and args.item_id.strip():
        p.error('create must not have --item-id')
    token = os.environ.get('QIITA_TOKEN')
    if not token:
        sys.exit('QIITA_TOKEN is missing (configure GitHub Actions secret).')
    root = Path(__file__).resolve().parents[1]
    body = (root / 'articles' / (args.article + '.md')).read_text(encoding='utf-8')
    if '【公開前に追記】' in body or '// ここに元の' in body:
        sys.exit('Article contains unverified placeholders. Please complete them before publishing.')
    meta = ARTICLES[args.article]
    payload = {'title': meta['title'], 'body': body, 'private': True,
               'tags': [{'name': tag} for tag in meta['tags']]}
    if args.operation == 'create':
        method, endpoint = 'POST', 'https://qiita.com/api/v2/items'
    else:
        method, endpoint = 'PATCH', 'https://qiita.com/api/v2/items/' + args.item_id.strip()
    request = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'), method=method,
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'User-Agent': 'qiita-articles-github-actions'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        print('Qiita API error:', exc.code, exc.read().decode('utf-8', errors='replace')[:1000], file=sys.stderr)
        sys.exit(1)
    print('Operation:', args.operation)
    print('Item ID:', result.get('id'))
    print('URL:', result.get('url'))
    print('Limited sharing:', result.get('private'))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write(f"### Qiita {args.operation}\n\n- Article: {args.article}\n- Item ID: `{result.get('id')}`\n- URL: {result.get('url')}\n- Limited sharing: {result.get('private')}\n")


if __name__ == '__main__':
    main()
