import json

with open('mapping.json', 'r', encoding='utf-8') as f:
    mapping = json.load(f)

mapping['✍'] = '/img/emojis/270d-fe0f.png'
mapping['🎙'] = '/img/emojis/1f399-fe0f.png'
mapping['🇬🇧'] = '/img/emojis/1f1ec-1f1e7.png'
mapping['🇺🇸'] = '/img/emojis/1f1fa-1f1f8.png'
mapping['✓'] = '/img/emojis/2714-fe0f.png' # map ✓ to check mark

with open('mapping.json', 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)
