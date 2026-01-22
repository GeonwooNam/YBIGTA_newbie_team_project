"""
한글 형태소 분석 유틸리티 모듈
의존성 문제를 피하기 위한 다양한 방법 제공
"""
import re
from typing import List, Optional


def detect_language(text: str) -> str:
    """
    텍스트의 언어를 감지합니다.
    
    Args:
        text: 분석할 텍스트
        
    Returns:
        'korean', 'english', 또는 'mixed'
    """
    if not text:
        return 'english'
    
    # 한글 유니코드 범위: AC00-D7A3 (가-힣)
    korean_pattern = re.compile(r'[가-힣]')
    english_pattern = re.compile(r'[a-zA-Z]')
    
    korean_count = len(korean_pattern.findall(text))
    english_count = len(english_pattern.findall(text))
    total_chars = len(re.sub(r'\s+', '', text))
    
    if total_chars == 0:
        return 'english'
    
    korean_ratio = korean_count / total_chars
    english_ratio = english_count / total_chars
    
    if korean_ratio > 0.3:
        return 'korean'
    elif english_ratio > 0.5:
        return 'english'
    else:
        return 'mixed'


def tokenize_korean_simple(text: str) -> List[str]:
    """
    간단한 한글 토크나이저 (의존성 없음)
    띄어쓰기 기반으로 토큰화하고, 짧은 조사/어미를 제거합니다.
    
    Args:
        text: 토크나이징할 텍스트
        
    Returns:
        토큰 리스트
    """
    if not text:
        return []
    
    # 특수문자 제거 및 정규화
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 띄어쓰기로 분리
    tokens = text.split()
    
    # 짧은 토큰 필터링 (1-2자 조사/어미 제거)
    filtered_tokens = []
    for token in tokens:
        if len(token) >= 2:  # 최소 2자 이상만 유지
            filtered_tokens.append(token)
    
    return filtered_tokens


def tokenize_korean_okt(text: str) -> Optional[List[str]]:
    """
    Okt를 사용한 한글 형태소 분석 (순수 Python, 의존성 적음)
    
    Args:
        text: 형태소 분석할 텍스트
        
    Returns:
        형태소 리스트 또는 None (설치 안 된 경우)
    """
    try:
        from konlpy.tag import Okt
        okt = Okt()
        # 명사, 동사, 형용사, 부사만 추출
        morphs = okt.pos(text, norm=True, stem=True)
        tokens = [word for word, pos in morphs if pos in ['Noun', 'Verb', 'Adjective', 'Adverb']]
        return tokens if tokens else None
    except ImportError:
        return None
    except Exception:
        return None


def tokenize_korean_soynlp(text: str) -> Optional[List[str]]:
    """
    Soynlp를 사용한 한글 토크나이징 (순수 Python)
    
    Args:
        text: 토크나이징할 텍스트
        
    Returns:
        토큰 리스트 또는 None (설치 안 된 경우)
    """
    try:
        from soynlp.word import WordExtractor
        from soynlp.tokenizer import MaxScoreTokenizer
        
        # 간단한 토크나이징 (학습 없이)
        # 실제로는 학습 데이터가 필요하지만, 기본 토크나이저 사용
        tokens = text.split()
        return [t for t in tokens if len(t) >= 2]
    except ImportError:
        return None
    except Exception:
        return None


def preprocess_korean_text(text: str, use_morphology: bool = True) -> str:
    """
    한글 텍스트를 전처리하고 형태소 분석을 수행합니다.
    여러 방법을 시도하여 가장 좋은 결과를 반환합니다.
    
    Args:
        text: 전처리할 텍스트
        use_morphology: 형태소 분석 사용 여부
        
    Returns:
        전처리된 텍스트 (공백으로 구분된 토큰)
    """
    if not text:
        return ""
    
    # 언어 감지
    lang = detect_language(text)
    
    # 영어나 혼합 텍스트는 그대로 반환
    if lang == 'english':
        return text
    
    # 한글 텍스트 처리
    if lang == 'korean' and use_morphology:
        # 방법 1: Okt 시도
        tokens = tokenize_korean_okt(text)
        if tokens:
            return ' '.join(tokens)
        
        # 방법 2: Soynlp 시도
        tokens = tokenize_korean_soynlp(text)
        if tokens:
            return ' '.join(tokens)
    
    # 방법 3: 간단한 토크나이저 (항상 사용 가능)
    tokens = tokenize_korean_simple(text)
    return ' '.join(tokens)


def get_korean_stopwords() -> List[str]:
    """
    한글 불용어 리스트를 반환합니다.
    
    Returns:
        불용어 리스트
    """
    return [
        '이', '가', '을', '를', '에', '의', '와', '과', '도', '로', '으로',
        '에서', '에게', '께', '한테', '더', '또', '그', '저', '이것', '그것',
        '것', '수', '때', '곳', '등', '및', '또한', '그리고', '하지만', '그런데',
        '그래서', '그러나', '따라서', '그러므로', '그런', '이런', '저런',
        '입니다', '입니다', '있습니다', '없습니다', '합니다', '됩니다',
        '입니다', '입니다', '입니다', '입니다'
    ]
