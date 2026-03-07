#!/usr/bin/env python3
"""
벡터DB에서 데이터를 추출하여 spec-account.md 포맷으로 저장하는 스크립트

입력:
- 벡터DB: chroma-agent
- 포맷: ph3-im/mw/spec/spec-account.md
- 저장: ph1-an/an2-requirement/spec-account01.md

처리:
1. 벡터DB에서 모든 데이터 조회
2. spec-account.md 포맷으로 변환
3. spec-account01.md 파일로 저장
"""

import chromadb
from chromadb.utils import embedding_functions
import os

def extract_vectordb_to_spec():
    """벡터DB에서 데이터를 추출하여 spec 포맷으로 저장"""
    
    print("=" * 60)
    print("벡터DB → Spec 포맷 변환 시작")
    print("=" * 60)
    
    # 1. ChromaDB 연결
    print("\n[1단계] ChromaDB 연결 중...")
    chroma_path = "/home/ec2-user/mcpsample/chroma-agent/chroma_store"
    
    if not os.path.exists(chroma_path):
        print(f"❌ 오류: ChromaDB 경로가 존재하지 않습니다: {chroma_path}")
        return
    
    client = chromadb.PersistentClient(path=chroma_path)
    
    # 임베딩 함수 설정
    sentence_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # 컬렉션 가져오기
    try:
        collection = client.get_collection(
            name="agent_knowledge",
            embedding_function=sentence_ef
        )
        print(f"✅ 컬렉션 'agent_knowledge' 연결 성공")
    except Exception as e:
        print(f"❌ 오류: 컬렉션을 가져올 수 없습니다: {e}")
        return
    
    # 2. 모든 데이터 조회
    print("\n[2단계] 벡터DB 데이터 조회 중...")
    try:
        # 컬렉션의 모든 데이터 가져오기
        all_data = collection.get()
        
        if not all_data or not all_data.get('ids'):
            print("❌ 벡터DB에 데이터가 없습니다.")
            return
        
        print(f"✅ 총 {len(all_data['ids'])}개의 문서 조회 완료")
        
        # 데이터 출력
        print("\n[조회된 데이터]")
        for i, (doc_id, document, metadata) in enumerate(zip(
            all_data['ids'], 
            all_data['documents'], 
            all_data['metadatas']
        ), 1):
            print(f"\n{i}. ID: {doc_id}")
            print(f"   문서: {document}")
            print(f"   메타데이터: {metadata}")
        
    except Exception as e:
        print(f"❌ 오류: 데이터 조회 실패: {e}")
        return
    
    # 3. Spec 포맷으로 변환
    print("\n[3단계] Spec 포맷으로 변환 중...")
    
    spec_content = generate_spec_format(all_data)
    
    # 4. 파일로 저장
    print("\n[4단계] 파일 저장 중...")
    output_path = "/home/ec2-user/mcpsample/ph1-an/an2-requirement/spec-account01.md"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        print(f"✅ 파일 저장 완료: {output_path}")
    except Exception as e:
        print(f"❌ 오류: 파일 저장 실패: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ 벡터DB → Spec 포맷 변환 완료!")
    print("=" * 60)


def generate_spec_format(data):
    """벡터DB 데이터를 spec-account.md 포맷으로 변환"""
    
    # spec-account.md 포맷 기반 템플릿
    spec_lines = []
    spec_lines.append("# 요구사항 정의서")
    spec_lines.append("")
    spec_lines.append("## 문서 정보")
    spec_lines.append("")
    
    # 페이지별로 데이터 정리
    pages = {}
    
    for doc_id, document, metadata in zip(
        data['ids'], 
        data['documents'], 
        data['metadatas']
    ):
        if metadata and metadata.get('type') == 'requirement':
            page = metadata.get('page', 'unknown')
            pages[page] = {
                'id': doc_id,
                'document': document,
                'metadata': metadata
            }
    
    # 페이지 순서대로 정렬
    sorted_pages = sorted(pages.items(), key=lambda x: x[0])
    
    # 각 페이지 내용 추가
    for page_num, page_data in sorted_pages:
        spec_lines.append(f"## 페이지 {page_num}")
        spec_lines.append("")
        
        # 메타데이터 정보
        metadata = page_data['metadata']
        spec_lines.append("### 메타데이터")
        spec_lines.append(f"  - 소스: {metadata.get('source', 'N/A')}")
        spec_lines.append(f"  - 파일명: {metadata.get('filename', 'N/A')}")
        spec_lines.append(f"  - 타입: {metadata.get('type', 'N/A')}")
        spec_lines.append("")
        
        # 문서 내용
        spec_lines.append("### 내용")
        spec_lines.append("```")
        spec_lines.append(page_data['document'])
        spec_lines.append("```")
        spec_lines.append("")
    
    # EC2 정보 추출 (페이지 004에서)
    if '004' in pages:
        spec_lines.append("## EC2 인프라 정보 (추출)")
        spec_lines.append("")
        spec_lines.append("페이지 004에서 추출된 EC2 정보:")
        spec_lines.append("")
        
        content = pages['004']['document']
        
        # Web1, Web2 정보 파싱
        if 'Web1' in content or 'Web2' in content:
            spec_lines.append("### Web 서버 정보")
            spec_lines.append("")
            
            # 간단한 파싱 (실제로는 더 정교한 파싱 필요)
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    spec_lines.append(f"  {line.strip()}")
            spec_lines.append("")
    
    # 요약 정보
    spec_lines.append("## 요약")
    spec_lines.append("")
    spec_lines.append(f"  - 총 페이지 수: {len(pages)}")
    spec_lines.append(f"  - 문서 타입: 요구사항 정의서")
    if sorted_pages:
        first_page = sorted_pages[0][1]
        source = first_page['metadata'].get('source', 'N/A')
        spec_lines.append(f"  - 소스 문서: {source}")
    spec_lines.append("")
    
    return '\n'.join(spec_lines)


if __name__ == "__main__":
    extract_vectordb_to_spec()
