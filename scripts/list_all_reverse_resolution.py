from django.urls import get_resolver, reverse
from django.urls.exceptions import NoReverseMatch


def get_all_url_patterns():
    resolver = get_resolver()  # URL resolver 가져오기
    patterns = resolver.url_patterns  # 모든 URL 패턴 가져오기
    return patterns


def resolve_all_urls():
    patterns = get_all_url_patterns()
    resolved_urls = []

    def _process_patterns(patterns, namespace=None):
        for pattern in patterns:
            if hasattr(pattern, 'url_patterns'):  # Include된 경우
                ns = f"{namespace}:{pattern.namespace}" if namespace else pattern.namespace
                _process_patterns(pattern.url_patterns, namespace=ns)
            elif pattern.name:  # 이름이 있는 URL 패턴
                try:
                    if namespace:
                        name = f"{namespace}:{pattern.name}"
                    else:
                        name = pattern.name
                    url = reverse(name)
                    resolved_urls.append((name, url))
                except NoReverseMatch:
                    resolved_urls.append((name, "NoReverseMatch"))

    _process_patterns(patterns)
    return resolved_urls


def run():
    urls = resolve_all_urls()
    filepath = "scripts/data/resolved_urls.txt"
    with open(filepath, "w", encoding="utf-8") as file:
        for name, url in urls:
            file.write(f"{name} → {url}\n")
